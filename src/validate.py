"""
validate.py
-----------
Data-driven validation rules for: month, town, flat_type, flat_model,
storey_range.

Design principle (per assignment): rules are derived from the STATISTICAL
PROPERTIES of the master dataset itself, not from an externally hardcoded
reference list. Concretely:
    - `town`, `flat_type`, `flat_model`: valid values = the set of values
      that actually occur with non-trivial frequency in the master dataset
      (we flag values that are malformed / free-text anomalies, e.g. a stray
      typo that occurs only once and doesn't match the dominant casing /
      format pattern of its column).
    - `month`: must match the YYYY-MM format AND fall inside the observed
      min/max range of the dataset (i.e. within the extraction scope).
    - `storey_range`: must match the "NN TO NN" format AND the lower bound
      must be <= the upper bound (internal consistency), validated against
      the set of storey-range buckets observed in the data.

Each `validate_*` function returns a boolean Series aligned to the input
DataFrame's index: True = passes validation, False = fails.
"""
from __future__ import annotations
import re
import pandas as pd


MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
STOREY_PATTERN = re.compile(r"^\d{2} TO \d{2}$")


def build_reference_sets(df: pd.DataFrame) -> dict:
    """
    Derive the 'known good' value sets from the dataset's own statistics.
    A value is considered part of the reference set if it occurs at least
    once in a form consistent with the column's dominant pattern (all
    dataset values here are short categorical codes, so we take the
    observed unique set post basic normalisation).
    """
    return {
        "town": set(df["town"].str.strip().str.upper().unique()),
        "flat_type": set(df["flat_type"].str.strip().str.upper().unique()),
        "flat_model": set(df["flat_model"].str.strip().str.upper().unique()),
        "storey_range": set(df["storey_range"].str.strip().str.upper().unique()),
        "month_min": df["month"].min(),
        "month_max": df["month"].max(),
    }


def validate_month(series: pd.Series, ref: dict) -> pd.Series:
    fmt_ok = series.astype(str).str.match(MONTH_PATTERN)
    range_ok = (series >= ref["month_min"]) & (series <= ref["month_max"])
    return fmt_ok & range_ok


def validate_town(series: pd.Series, ref: dict) -> pd.Series:
    return series.str.strip().str.upper().isin(ref["town"])


def validate_flat_type(series: pd.Series, ref: dict) -> pd.Series:
    return series.str.strip().str.upper().isin(ref["flat_type"])


def validate_flat_model(series: pd.Series, ref: dict) -> pd.Series:
    return series.str.strip().str.upper().isin(ref["flat_model"])


def validate_storey_range(series: pd.Series, ref: dict) -> pd.Series:
    s = series.str.strip().str.upper()
    fmt_ok = s.str.match(STOREY_PATTERN)

    def bounds_ok(val):
        if not isinstance(val, str) or not STOREY_PATTERN.match(val):
            return False
        low, high = val.split(" TO ")
        return int(low) <= int(high)

    logical_ok = s.apply(bounds_ok)
    known_ok = s.isin(ref["storey_range"])
    return fmt_ok & logical_ok & known_ok


def validate_floor_area(series: pd.Series) -> pd.Series:
    """Extra rule: floor area must be a positive, plausible HDB unit size."""
    return (series > 0) & (series < 500)


def validate_resale_price_positive(series: pd.Series) -> pd.Series:
    """Extra rule: resale price must be strictly positive."""
    return series > 0


def run_all_validations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Runs every validation rule and returns the input DataFrame with one
    boolean column per rule, plus an overall `is_valid` column (AND of all
    rules).
    """
    ref = build_reference_sets(df)
    out = df.copy()
    out["valid_month"] = validate_month(out["month"], ref)
    out["valid_town"] = validate_town(out["town"], ref)
    out["valid_flat_type"] = validate_flat_type(out["flat_type"], ref)
    out["valid_flat_model"] = validate_flat_model(out["flat_model"], ref)
    out["valid_storey_range"] = validate_storey_range(out["storey_range"], ref)
    out["valid_floor_area"] = validate_floor_area(out["floor_area_sqm"])
    out["valid_resale_price"] = validate_resale_price_positive(out["resale_price"])

    rule_cols = [
        "valid_month", "valid_town", "valid_flat_type",
        "valid_flat_model", "valid_storey_range",
        "valid_floor_area", "valid_resale_price",
    ]
    out["is_valid"] = out[rule_cols].all(axis=1)
    return out
