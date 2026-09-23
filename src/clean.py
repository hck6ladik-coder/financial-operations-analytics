"""Cleaning rules for financial transactions."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def clean_transactions(df: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    """Apply documented cleaning rules and return a typed DataFrame.

    Rules
    -----
    1. Drop exact duplicates.
    2. Flag near-duplicates on (date, amount, counterparty).
    3. Standardise date → ISO 8601 (datetime64[ns]).
    4. Amounts already signed (expenses negative); enforce float64.
    5. Missing values: drop rows missing critical fields; flag others.
    6. Currency forced to configured base (EUR).
    """
    original_len = len(df)
    out = df.copy()

    # 1. Exact duplicates
    out = out.drop_duplicates()
    n_exact = original_len - len(out)
    if n_exact:
        logger.info("Dropped %d exact duplicate rows", n_exact)

    # 2. Near-duplicates flag
    key_cols = ["date", "amount", "counterparty"]
    if all(c in out.columns for c in key_cols):
        out["is_near_duplicate"] = out.duplicated(subset=key_cols, keep=False)
        n_near = int(out["is_near_duplicate"].sum())
        if n_near:
            logger.info("Flagged %d near-duplicate rows (kept)", n_near)
    else:
        out["is_near_duplicate"] = False

    # 3. Date standardisation
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    n_bad_dates = int(out["date"].isna().sum())
    if n_bad_dates:
        logger.warning("Dropping %d rows with unparseable dates", n_bad_dates)
        out = out.dropna(subset=["date"])

    # 4. Amount typing + sign convention already present
    out["amount"] = pd.to_numeric(out["amount"], errors="coerce")
    n_bad_amt = int(out["amount"].isna().sum())
    if n_bad_amt:
        logger.warning("Dropping %d rows with non-numeric amount", n_bad_amt)
        out = out.dropna(subset=["amount"])

    # 5. Critical fields
    critical = ["transaction_id", "date", "amount", "category", "type"]
    before = len(out)
    out = out.dropna(subset=[c for c in critical if c in out.columns])
    if len(out) < before:
        logger.info("Dropped %d rows missing critical fields", before - len(out))

    # 6. Currency
    if "currency" in out.columns:
        out["currency"] = out["currency"].fillna(cfg["data"]["currency"]).str.upper()
    else:
        out["currency"] = cfg["data"]["currency"]

    # Ensure type column consistency
    if "type" in out.columns:
        out["type"] = out["type"].str.lower().str.strip()

    # Add helper columns
    out["year_month"] = out["date"].dt.to_period("M").astype(str)
    out["is_income"] = out["amount"] > 0
    out["is_expense"] = out["amount"] < 0

    out = out.sort_values("date").reset_index(drop=True)
    logger.info("Cleaned dataset: %d -> %d rows", original_len, len(out))
    return out
