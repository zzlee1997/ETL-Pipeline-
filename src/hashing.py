"""
hashing.py
----------
Irreversibly hashes the `resale_identifier` column while preserving its
uniqueness property.

Algorithm chosen: SHA-256.
    - Cryptographically irreversible (one-way): given a hash output, it is
      computationally infeasible to recover the original identifier.
    - Preserves uniqueness for our purposes: SHA-256 has a 256-bit output
      space (2^256 possible digests). For a dataset of ~100K-1M rows, the
      probability of an accidental collision is astronomically small
      (by the birthday bound, ~n^2 / 2^257), so distinct identifiers will
      produce distinct hashes with overwhelming probability in practice.
    - Deterministic: the same identifier always hashes to the same digest,
      which is required so the hashed column remains a valid, consistent
      join/reference key downstream.

Note: SHA-256 alone is unsalted, so it is technically vulnerable to a
dictionary/rainbow-table attack if the space of possible identifiers were
small and guessable. Do note that the identifiers are structured and
this hashing step exists to satisfy the assignment's "irreversible
hashing" requirement for output governance -- not to protect a secret --
so plain SHA-256 is an appropriate, standard choice here. (If identifier
confidentiality against guessing were a hard requirement, an HMAC with a
private key would be the appropriate upgrade.)
"""
from __future__ import annotations
import hashlib
import pandas as pd


def hash_identifier(identifier: str) -> str:
    return hashlib.sha256(identifier.encode("utf-8")).hexdigest()


def add_hashed_identifier(df: pd.DataFrame, source_col: str = "resale_identifier") -> pd.DataFrame:
    df = df.copy()
    df["hashed_identifier"] = df[source_col].apply(hash_identifier)

    n_total = len(df)
    n_unique_source = df[source_col].nunique()
    n_unique_hash = df["hashed_identifier"].nunique()
    assert n_unique_source == n_unique_hash, (
        f"Hash collision detected: {n_unique_source} unique identifiers "
        f"produced only {n_unique_hash} unique hashes (out of {n_total} rows)."
    )
    return df
