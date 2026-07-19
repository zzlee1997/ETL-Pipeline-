# HDB Resale Flat Prices — ETL Pipeline

Data Engineering Team submission — Part 1: Developing Data Pipelines.

## Scope
January 2012 – December 2016 HDB resale flat transactions, sourced from
[data.gov.sg — Resale Flat Prices](https://data.gov.sg/collections/189/view).

## How to run
```
pip install pandas jupyter nbformat
cd notebooks
jupyter nbconvert --to notebook --execute --inplace ETL_Pipeline.ipynb
# or just open ETL_Pipeline.ipynb in Jupyter and Run All
* Note that the scripts within the src folder are modular scripts imported into the ipynb script for the ETL-Pipeline to run the tasks. Hence, they should be downloaded within the same main folder to run the ipynb file on Jupyter Notebook *
```
No manual data editing is required or performed anywhere in the pipeline — every source
file in `data/raw/` is loaded and processed exactly as downloaded.

## Project structure
```
ETL-Pipeline-/
├── data/raw # contains all initial raw files (note that data/raw means a "raw" folder within the "data" folder)
├── src/                   # reusable, documented pipeline logic
│   ├── extract.py         # load + union raw files, scope-filter to Jan 2012 - Dec 2016
│   ├── profiling.py       # lightweight column-level data profiling
│   ├── validate.py        # data-driven validation rules
│   ├── dedup.py            # composite-key duplicate resolution
│   ├── lease.py            # remaining lease recomputation (99-year lease assumption)
│   ├── anomaly.py          # peer-group Z-score price anomaly detection
│   ├── transform.py        # Resale Identifier derivation + identifier-level dedup
│   └── hashing.py          # SHA-256 identifier hashing
├── notebooks/
│   └── ETL_Pipeline.ipynb  # orchestrates src/ modules, documents every decision inline
├── outputs/
│   ├── raw/                # downloaded copies of source files
│   ├── cleaned/             # passed all data quality rules
│   ├── failed/               # rejected records, tagged with failure_reason
│   ├── transformed/          # cleaned data + Resale Identifier column
│   └── hashed/                # cleaned data + hashed identifier column
│   ├── profiling_report.csv  # per-column data profile
│   └── pipeline_summary.csv  # row counts at every pipeline stage
└── README.md
```

## Source file scope note
data.gov.sg splits this dataset across several files by date range. To cover
Jan 2012 – Dec 2016 exactly that is needed: the **tail end (Jan–Feb 2012 only)** of the
"Approval_Date 2000 – Feb 2012" file, plus the full "Registration_Date Mar 2012 – Dec 2014"
and "Registration_Date Jan 2015 – Dec 2016" files. The out-of-scope "Approval_Date 1990–1999"
file is loaded (not manually excluded) and is naturally dropped by the same programmatic
`month` range filter — see `extract.build_master_dataset`.

## Key design decisions & assumptions
| Area | Decision |
|---|---|
| **Composite key** | All columns except `resale_price` **and** the source `remaining_lease` column (which I discarded and recompute ourselves — see below). |
| **Remaining lease** | `lease_commence_date` is year-only, so I assumed commencement on 1 Jan of that year. Remaining lease = (`lease_commence_date` + 99) − today, floored down to whole years + months. |
| **Validation rules** | `town`, `flat_type`, `flat_model`, `storey_range` are validated against the *observed* value set in the master dataset itself (not an external hardcoded list); `month` and `storey_range` also get format/logical checks (regex + lower ≤ upper bound). Extra rules added for `floor_area_sqm` and `resale_price` positivity/plausibility. |
| **Anomalous price heuristic** | Z-score of `resale_price` within peer group (`town` + `flat_type` + `flat_model`); flagged if \|Z\| > 3 and peer group has ≥ 5 observations. Anomalies are flagged, not dropped. |
| **Resale Identifier** | 9 characters: `S` + 3-digit block (digits-only, zero-padded) + first 2 digits of the peer-group (month, town, flat_type) average price + row's own 2-digit month + town's first letter. See `src/transform.py` docstring for worked examples. |
| **Hashing** | SHA-256 — irreversible, 256-bit space makes collisions practically impossible at this dataset size, deterministic. See `src/hashing.py` docstring for the full rationale, including why plain SHA-256 (vs. HMAC) is appropriate here. |

## Pipeline result summary
See `outputs/pipeline_summary.csv` for exact row counts through every stage (extraction →
validation → composite-key dedup → identifier derivation → identifier dedup → hashing).
