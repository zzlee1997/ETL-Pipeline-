"""
dedup.py
--------
Composite-key duplicate resolution.

Per assignment: "the composite key for the dataset is all columns except the
resale price. If all columns have the exact same value, except for the
resale price (duplicated key), take the higher price and discard the lower
price into the failed dataset."

We define the composite key as every business/identifying column EXCLUDING:
    - resale_price (explicitly excluded per spec)
    - remaining_lease (source-provided; we discard this column entirely and
      recompute our own remaining_lease_years/months downstream, so it is
      not part of row identity)
"""
from __future__ import annotations
import pandas as pd

NON_KEY_COLUMNS = {"resale_price", "remaining_lease"}


def get_key_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in NON_KEY_COLUMNS]


def resolve_duplicates(df: pd.DataFrame, key_cols: list[str] | None = None):
    """
    For rows sharing the same composite key, keep only the row with the
    highest resale_price. All other (lower-price) rows in that group are
    routed to the `failed` set with a reason tag.

    Returns
    -------
    kept_df : pd.DataFrame
        One row per unique composite key (the highest-price row of each group).
    failed_df : pd.DataFrame
        The discarded lower-price duplicate rows, with a `failure_reason` column.
    """
    if key_cols is None:
        key_cols = get_key_columns(df)

    df = df.copy()
    # Rank rows within each key group by resale_price, descending.
    df["_rank_in_group"] = (
        df.groupby(key_cols)["resale_price"].rank(method="first", ascending=False)
    )

    kept_df = df[df["_rank_in_group"] == 1].drop(columns=["_rank_in_group"]).copy()
    failed_df = df[df["_rank_in_group"] != 1].drop(columns=["_rank_in_group"]).copy()
    if len(failed_df):
        failed_df["failure_reason"] = "duplicate_composite_key_lower_price"

    return kept_df.reset_index(drop=True), failed_df.reset_index(drop=True)
