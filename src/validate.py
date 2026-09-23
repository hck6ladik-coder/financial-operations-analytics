"""Schema and business-rule validation (fail-fast)."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import pandera.pandas as pa
from pandera.typing import Series

logger = logging.getLogger(__name__)


class TransactionSchema(pa.DataFrameModel):
    """Pandera schema contract for cleaned transactions."""

    transaction_id: Series[str] = pa.Field(nullable=False, unique=True)
    date: Series[pd.Timestamp] = pa.Field(nullable=False)
    amount: Series[float] = pa.Field(nullable=False)
    currency: Series[str] = pa.Field(nullable=False)
    category: Series[str] = pa.Field(nullable=False)
    counterparty: Series[str] = pa.Field(nullable=True)
    account: Series[str] = pa.Field(nullable=True)
    description: Series[str] = pa.Field(nullable=True)
    type: Series[str] = pa.Field(nullable=False)
    is_near_duplicate: Series[bool] = pa.Field(nullable=True)
    year_month: Series[str] = pa.Field(nullable=True)
    is_income: Series[bool] = pa.Field(nullable=True)
    is_expense: Series[bool] = pa.Field(nullable=True)

    class Config:
        strict = False
        coerce = True


def validate_transactions(df: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    """Validate against schema and range contracts. Raises on failure."""
    vcfg = cfg["validation"]

    # Column presence
    missing = set(vcfg["required_columns"]) - set(df.columns)
    if missing:
        raise ValueError(f"Schema violation — missing columns: {sorted(missing)}")

    # Allowed value sets (driven by config.yaml)
    allowed_currencies = set(vcfg["allowed_currencies"])
    bad_currencies = sorted(set(df["currency"].dropna()) - allowed_currencies)
    if bad_currencies:
        raise ValueError(
            f"Currency violation — not in allowed_currencies {sorted(allowed_currencies)}: "
            f"{bad_currencies}"
        )

    allowed_types = set(vcfg["allowed_types"])
    bad_types = sorted(set(df["type"].dropna()) - allowed_types)
    if bad_types:
        raise ValueError(
            f"Type violation — not in allowed_types {sorted(allowed_types)}: {bad_types}"
        )

    # Range checks
    amt_min, amt_max = vcfg["amount_min"], vcfg["amount_max"]
    out_of_range = df[(df["amount"] < amt_min) | (df["amount"] > amt_max)]
    if not out_of_range.empty:
        examples = out_of_range[["transaction_id", "amount"]].head(3).to_dict("records")
        raise ValueError(f"Amount range violation ({amt_min}..{amt_max}). Examples: {examples}")

    # Pandera
    try:
        validated = TransactionSchema.validate(df, lazy=True)
    except pa.errors.SchemaErrors as exc:
        logger.error("Schema validation failed:\n%s", exc.failure_cases.head(10))
        raise ValueError(f"Pandera schema errors: {len(exc.failure_cases)} failures") from exc

    # Referential-ish checks
    if validated["type"].eq("income").sum() == 0:
        logger.warning("No income transactions found — check data quality")
    if validated["type"].eq("expense").sum() == 0:
        logger.warning("No expense transactions found — check data quality")

    logger.info("Validation passed for %d rows", len(validated))
    return validated
