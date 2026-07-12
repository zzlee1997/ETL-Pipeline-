"""
extract.py
----------
Load raw HDB resale price CSV files "as-is" and union them into a single
master dataset covering the required scope: January 2012 - December 2016.

data.gov.sg publishes this dataset split across several files by date range.
For our required scope we need parts of two files:
    - "...Approval_Date___2000_-_Feb_2012.csv"   -> only rows for 2012-01, 2012-02
    - "...Registration_Date___From_Mar_2012_to_Dec_2014.csv" -> used in full
    - "...Registration_Date___From_Jan_2015_to_Dec_2016.csv" -> used in full

No manual editing of the source files is performed. Filtering to the
Jan-2012-Dec-2016 scope is done programmatically, in code, based on the
`month` column -- not by deleting rows/files by hand.
"""
from __future__ import annotations
import glob
import os
import pandas as pd

SCOPE_START = "2012-01"
SCOPE_END = "2016-12"


def load_raw_files(raw_dir: str) -> dict[str, pd.DataFrame]:
    """Load every CSV in `raw_dir` into a dict keyed by filename, untouched."""
    frames = {}
    for path in sorted(glob.glob(os.path.join(raw_dir, "*.csv"))):
        name = os.path.basename(path)
        frames[name] = pd.read_csv(path, dtype={"block": str})
    return frames


def build_master_dataset(raw_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Union all raw frames (outer join on columns, so any attribute present in
    ANY file is preserved for ALL rows -- missing values become NaN), then
    filter programmatically to the Jan 2012 - Dec 2016 scope.
    """
    all_frames = list(raw_frames.values())
    master = pd.concat(all_frames, ignore_index=True, sort=False)

    # Programmatic scope filter (not a manual row deletion -- a coded rule).
    master = master[
        (master["month"] >= SCOPE_START) & (master["month"] <= SCOPE_END)
    ].reset_index(drop=True)

    return master
