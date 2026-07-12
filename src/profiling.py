"""
profiling.py
------------
Lightweight, dependency-free data profiling (no external profiling library
required, so the notebook has no heavy/fragile dependencies). Produces a
per-column summary: dtype, null count/%, distinct count, and for numeric
columns min/mean/median/max/std, for categorical columns the top values.
"""
from __future__ import annotations
import pandas as pd


def profile_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n = len(df)
    for col in df.columns:
        s = df[col]
        row = {
            "column": col,
            "dtype": str(s.dtype),
            "n_null": s.isnull().sum(),
            "pct_null": round(100 * s.isnull().sum() / n, 2) if n else 0,
            "n_distinct": s.nunique(dropna=True),
        }
        if pd.api.types.is_numeric_dtype(s):
            row.update({
                "min": s.min(),
                "mean": round(s.mean(), 2) if s.notna().any() else None,
                "median": s.median(),
                "max": s.max(),
                "std": round(s.std(), 2) if s.notna().any() else None,
                "top_values": None,
            })
        else:
            top = s.value_counts(dropna=True).head(5)
            row.update({
                "min": None, "mean": None, "median": None, "max": None, "std": None,
                "top_values": "; ".join(f"{k} ({v})" for k, v in top.items()),
            })
        rows.append(row)
    return pd.DataFrame(rows)
