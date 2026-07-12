"""
anomaly.py
----------
Anomalous resale price detection.

Heuristic & assumptions (documented per assignment requirement):
    A resale price is only "anomalous" relative to comparable flats -- a
    price that's normal for a 5-room Bishan flat would be wildly anomalous
    for a 2-room Woodlands flat. We therefore compute a Z-score for each
    row's resale_price WITHIN its peer group, defined as:

        peer group = (town, flat_type, flat_model)

    Z-score = (price - group_mean) / group_std

    A row is flagged anomalous if |Z-score| > 3 (the standard "3-sigma"
    convention for outliers under an assumed-normal distribution), AND the
    peer group has at least `min_group_size` observations (default 5) --
    below that, a standard deviation is too noisy to be meaningful, so we
    do not flag small groups as anomalous purely on Z-score grounds.
"""
from __future__ import annotations
import pandas as pd

PEER_GROUP_COLS = ["town", "flat_type", "flat_model"]


def flag_price_anomalies(
    df: pd.DataFrame,
    z_threshold: float = 3.0,
    min_group_size: int = 5,
) -> pd.DataFrame:
    """
    Adds `price_zscore` and `is_price_anomaly` columns.
    """
    df = df.copy()
    grouped = df.groupby(PEER_GROUP_COLS)["resale_price"]

    group_stats = grouped.transform("mean").rename("group_mean")
    group_std = grouped.transform("std").rename("group_std")
    group_size = grouped.transform("size").rename("group_size")

    df["_group_mean"] = group_stats
    df["_group_std"] = group_std
    df["_group_size"] = group_size

    # Avoid divide-by-zero for peer groups with zero variance.
    safe_std = df["_group_std"].replace(0, pd.NA)
    df["price_zscore"] = (df["resale_price"] - df["_group_mean"]) / safe_std
    df["price_zscore"] = df["price_zscore"].fillna(0.0)

    df["is_price_anomaly"] = (
        (df["price_zscore"].abs() > z_threshold) & (df["_group_size"] >= min_group_size)
    )

    df = df.drop(columns=["_group_mean", "_group_std", "_group_size"])
    return df
