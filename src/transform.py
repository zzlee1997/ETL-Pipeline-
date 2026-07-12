"""
transform.py
------------
Derives the "Resale Identifier" column per the assignment's exact spec.

Format (9 characters total): S + BBB + PP + MM + T
    S    : literal "S"
    BBB  : first 3 digits of `block`, after stripping any non-digit
           characters, left-padded with zeros if fewer than 3 digits remain
           (e.g. block "19" -> "019"; block "104A" -> strip letters -> "104"
           -> already 3 digits -> "104"; block "94E" -> "94" -> pad -> "094")
    PP   : first 2 digits of the AVERAGE resale price for this row's
           (year-month, town, flat_type) peer group (e.g. avg price 230000
           -> "23")
    MM   : the 2-digit month of THIS row's own `month` entry (e.g. "2012-01"
           -> "01") -- note this is the row's own month, not the group's
    T    : first character of `town`

Assumption: the "average resale price grouped by year-month, town,
flat_type" is computed over the dataset being transformed (i.e. the cleaned
dataset at the point the identifier is generated), so the peer average
reflects this pipeline run's own data.
"""
from __future__ import annotations
import re
import pandas as pd

DIGIT_PATTERN = re.compile(r"\d")


def _block_digits(block: str) -> str:
    digits = "".join(re.findall(r"\d", str(block)))
    if len(digits) < 3:
        return digits.zfill(3)
    return digits[:3]


def add_resale_identifier(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # --- BBB: block digits ---
    block_part = df["block"].apply(_block_digits)

    # --- PP: first 2 digits of avg resale price, grouped by (month, town, flat_type) ---
    group_avg = (
        df.groupby(["month", "town", "flat_type"])["resale_price"]
        .transform("mean")
    )
    price_part = group_avg.round(0).astype("int64").astype(str).str[:2]

    # --- MM: this row's own month ---
    month_part = df["month"].str.split("-").str[1]

    # --- T: first character of town ---
    town_part = df["town"].str[0]

    df["resale_identifier"] = (
        "S" + block_part + price_part + month_part + town_part
    )
    return df


def resolve_identifier_duplicates(df: pd.DataFrame):
    """
    Step 2 of the Transformation requirements: if the newly-derived
    `resale_identifier` produces duplicates, keep the higher resale_price
    row and discard the rest to `failed`. This is a distinct, idempotent
    dedup pass keyed on the identifier itself (not the full composite key
    used earlier in cleaning).
    """
    df = df.copy()
    df["_rank_in_group"] = (
        df.groupby("resale_identifier")["resale_price"]
        .rank(method="first", ascending=False)
    )
    kept = df[df["_rank_in_group"] == 1].drop(columns=["_rank_in_group"]).copy()
    failed = df[df["_rank_in_group"] != 1].drop(columns=["_rank_in_group"]).copy()
    if len(failed):
        failed["failure_reason"] = "duplicate_resale_identifier_lower_price"
    return kept.reset_index(drop=True), failed.reset_index(drop=True)
