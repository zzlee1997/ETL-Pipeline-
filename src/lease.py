"""
lease.py
--------
Recompute HDB remaining lease as of a reference date (default: today).

Assumption (documented per assignment requirement):
    The source data only provides `lease_commence_date` as a YEAR (e.g. 1986),
    not a full date. We assume every lease commences on 1 January of that year.
    This is the same convention HDB / data.gov.sg implicitly uses when they
    publish a `remaining_lease` column expressed in whole years (+ months).

    remaining_lease = (lease_commence_year + 99)  MINUS  as_of_date
    expressed as whole years and whole months, FLOORED DOWN (i.e. any partial
    month remaining is dropped, never rounded up).

We deliberately ignore the `remaining_lease` column that ships with the
2015-2016 source file: it is only present in one of our source files, would
be "as at extraction date" (not standardized to our own reference date), and
the assignment explicitly asks us to recompute it ourselves for consistency
across every year in the master dataset.
"""
from __future__ import annotations
from datetime import date
from typing import Tuple


def compute_remaining_lease(
    lease_commence_year: int,
    as_of_date: date | None = None,
    lease_term_years: int = 99,
) -> Tuple[int, int]:
    """
    Compute remaining lease (years, months) as of `as_of_date`, floored down.

    Parameters
    ----------
    lease_commence_year : int
        The year the lease commenced (assumed 1 Jan of that year).
    as_of_date : date, optional
        Reference date to compute remaining lease against. Defaults to today.
    lease_term_years : int
        Total lease term. Defaults to 99 (standard HDB lease).

    Returns
    -------
    (years, months) : Tuple[int, int]
        Whole years and whole months remaining, floored down. Never negative
        (clamped to (0, 0) for leases that have already expired).
    """
    if as_of_date is None:
        as_of_date = date.today()

    lease_end = date(lease_commence_year + lease_term_years, 1, 1)

    total_months_remaining = (
        (lease_end.year - as_of_date.year) * 12
        + (lease_end.month - as_of_date.month)
    )

    # Both lease_end and as_of_date are compared at day-of-month granularity
    # only when day counts would flip a boundary month; since lease_end's day
    # is always 1, subtract one more month if as_of_date's day > 1 (i.e. we
    # haven't yet reached the 1st of this month's anniversary) -- this keeps
    # the "floor down, never round up" guarantee exact.
    if as_of_date.day > 1:
        total_months_remaining -= 1

    total_months_remaining = max(total_months_remaining, 0)

    years, months = divmod(total_months_remaining, 12)
    return years, months


def add_remaining_lease_columns(df, lease_col="lease_commence_date", as_of_date=None):
    """
    Vectorized-friendly helper: adds `remaining_lease_years` and
    `remaining_lease_months` columns to a DataFrame, plus a combined
    human-readable `remaining_lease_display` string (e.g. "61 years 4 months").
    """
    results = df[lease_col].apply(
        lambda y: compute_remaining_lease(int(y), as_of_date=as_of_date)
    )
    df = df.copy()
    df["remaining_lease_years"] = results.apply(lambda t: t[0])
    df["remaining_lease_months"] = results.apply(lambda t: t[1])
    df["remaining_lease_display"] = df.apply(
        lambda r: f"{r['remaining_lease_years']} years {r['remaining_lease_months']} months",
        axis=1,
    )
    return df
