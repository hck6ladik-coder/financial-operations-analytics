"""Tests for validation logic — edge cases and business rules."""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from src.clean import clean_transactions
from src.validate import validate_transactions


def _clean_df(cfg: dict[str, Any]) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "transaction_id": [f"T{i:03d}" for i in range(1, 11)],
            "date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "amount": [100.0, -50.0, -30.0, 200.0, -10.0, 500.0, -75.0, 300.0, -20.0, 150.0],
            "currency": ["EUR"] * 10,
            "category": [
                "Salary",
                "Groceries",
                "Dining",
                "Salary",
                "Transport",
                "Salary",
                "Dining",
                "Salary",
                "Groceries",
                "Transport",
            ],
            "counterparty": ["A"] * 10,
            "account": ["X"] * 10,
            "description": ["desc"] * 10,
            "type": [
                "income",
                "expense",
                "expense",
                "income",
                "expense",
                "income",
                "expense",
                "income",
                "expense",
                "expense",
            ],
        }
    )
    return clean_transactions(df, cfg)


def test_validate_passes(cfg: dict[str, Any]) -> None:
    clean_df = _clean_df(cfg)
    result = validate_transactions(clean_df, cfg)
    assert len(result) == len(clean_df)


def test_validate_missing_column(cfg: dict[str, Any]) -> None:
    bad = _clean_df(cfg).drop(columns=["category"])
    with pytest.raises(ValueError, match="missing columns"):
        validate_transactions(bad, cfg)


def test_validate_out_of_range(cfg: dict[str, Any]) -> None:
    bad = _clean_df(cfg)
    bad.loc[0, "amount"] = 999999.0
    with pytest.raises(ValueError, match="range violation"):
        validate_transactions(bad, cfg)


def test_validate_invalid_currency(cfg: dict[str, Any]) -> None:
    bad = _clean_df(cfg)
    bad.loc[0, "currency"] = "USD"
    with pytest.raises(ValueError, match="Currency violation"):
        validate_transactions(bad, cfg)


def test_validate_invalid_type(cfg: dict[str, Any]) -> None:
    bad = _clean_df(cfg)
    bad.loc[0, "type"] = "transfer"
    with pytest.raises(ValueError, match="Type violation"):
        validate_transactions(bad, cfg)


def test_schema_unique_transaction_ids(cfg: dict[str, Any]) -> None:
    bad = _clean_df(cfg)
    bad.loc[0, "transaction_id"] = bad.loc[1, "transaction_id"]
    with pytest.raises(ValueError):
        validate_transactions(bad, cfg)


def test_no_income_warning(cfg: dict[str, Any]) -> None:
    no_income = _clean_df(cfg)
    no_income = no_income[no_income["type"] == "expense"].copy()
    result = validate_transactions(no_income, cfg)
    assert len(result) > 0


def test_empty_dataframe_passes(cfg: dict[str, Any]) -> None:
    empty = pd.DataFrame(
        columns=[
            "transaction_id",
            "date",
            "amount",
            "currency",
            "category",
            "counterparty",
            "account",
            "description",
            "type",
            "is_near_duplicate",
            "year_month",
            "is_income",
            "is_expense",
        ]
    )
    result = validate_transactions(empty, cfg)
    assert len(result) == 0


def test_allowed_currencies_comes_from_config(cfg: dict[str, Any]) -> None:
    """Widening allowed_currencies in config must change validation behaviour."""
    cfg["validation"]["allowed_currencies"] = ["EUR", "USD"]
    bad = _clean_df(cfg)
    bad.loc[0, "currency"] = "USD"
    result = validate_transactions(bad, cfg)
    assert (result["currency"] == "USD").any()
