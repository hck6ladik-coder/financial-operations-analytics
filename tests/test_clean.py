"""Tests for cleaning logic."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.clean import clean_transactions


def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "transaction_id": ["T1", "T2", "T2", "T3", "T4"],
            "date": ["2024-01-15", "2024-01-16", "2024-01-16", "bad-date", "2024-02-01"],
            "amount": [100.0, -50.0, -50.0, 20.0, None],
            "currency": ["EUR", "EUR", "EUR", "EUR", "EUR"],
            "category": ["Salary", "Groceries", "Groceries", "Dining", "Rent"],
            "counterparty": ["A", "B", "B", "C", "D"],
            "account": ["X", "X", "X", "X", "X"],
            "description": ["s", "g", "g", "d", "r"],
            "type": ["income", "expense", "expense", "expense", "expense"],
        }
    )


def test_drops_exact_duplicates(cfg: dict[str, Any]) -> None:
    out = clean_transactions(sample_df(), cfg)
    # one of the two identical T2 rows is dropped
    assert out["transaction_id"].tolist().count("T2") == 1
    assert len(out) == 2  # T1, T2 survive (T3 bad date, T4 null amount)


def test_date_parsed(cfg: dict[str, Any]) -> None:
    out = clean_transactions(sample_df(), cfg)
    assert pd.api.types.is_datetime64_any_dtype(out["date"])


def test_critical_nulls_dropped(cfg: dict[str, Any]) -> None:
    out = clean_transactions(sample_df(), cfg)
    assert out["amount"].notna().all()
    assert "bad-date" not in out["date"].astype(str).values


def test_all_duplicate_rows(cfg: dict[str, Any]) -> None:
    dup = pd.DataFrame(
        {
            "transaction_id": ["T1"] * 3,
            "date": ["2024-01-15"] * 3,
            "amount": [100.0] * 3,
            "currency": ["EUR"] * 3,
            "category": ["Salary"] * 3,
            "counterparty": ["A"] * 3,
            "account": ["X"] * 3,
            "description": ["s"] * 3,
            "type": ["income"] * 3,
        }
    )
    out = clean_transactions(dup, cfg)
    assert len(out) == 1


def test_amount_typed_float64(cfg: dict[str, Any]) -> None:
    out = clean_transactions(sample_df(), cfg)
    assert pd.api.types.is_float_dtype(out["amount"])


def test_currency_uppercased(cfg: dict[str, Any]) -> None:
    df = sample_df()
    df.loc[0, "currency"] = "eur"
    out = clean_transactions(df, cfg)
    assert out["currency"].iloc[0] == "EUR"


def test_type_lowercased(cfg: dict[str, Any]) -> None:
    df = sample_df()
    df.loc[0, "type"] = "INCOME"
    out = clean_transactions(df, cfg)
    assert out["type"].iloc[0] == "income"


def test_year_month_added(cfg: dict[str, Any]) -> None:
    out = clean_transactions(sample_df(), cfg)
    assert "year_month" in out.columns
    assert out["year_month"].iloc[0] == "2024-01"


def test_is_income_is_expense_flags(cfg: dict[str, Any]) -> None:
    out = clean_transactions(sample_df(), cfg)
    assert "is_income" in out.columns
    assert "is_expense" in out.columns
    assert out["is_income"].dtype == bool
    assert out["is_expense"].dtype == bool


def test_empty_dataframe(cfg: dict[str, Any]) -> None:
    """Empty input with proper columns should produce empty output."""
    empty = pd.DataFrame(
        columns=["transaction_id", "date", "amount", "currency", "category", "type"]
    )
    out = clean_transactions(empty, cfg)
    assert len(out) == 0


def test_all_income_no_expenses(cfg: dict[str, Any]) -> None:
    income_df = pd.DataFrame(
        {
            "transaction_id": ["T1", "T2"],
            "date": ["2024-01-15", "2024-01-16"],
            "amount": [100.0, 200.0],
            "currency": ["EUR", "EUR"],
            "category": ["Salary", "Freelance"],
            "counterparty": ["A", "B"],
            "account": ["X", "X"],
            "description": ["s", "g"],
            "type": ["income", "income"],
        }
    )
    out = clean_transactions(income_df, cfg)
    assert len(out) == 2
    assert (out["amount"] > 0).all()


def test_sorted_by_date(cfg: dict[str, Any]) -> None:
    out = clean_transactions(sample_df(), cfg)
    assert out["date"].is_monotonic_increasing
