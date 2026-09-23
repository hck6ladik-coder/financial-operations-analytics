"""Tests for transform layer (monthly / category / rolling features)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.transform import add_rolling_features, build_category_summary, build_monthly_summary


def _transactions() -> pd.DataFrame:
    dates = pd.to_datetime(["2024-01-05", "2024-01-10", "2024-01-20", "2024-02-05", "2024-02-15"])
    return pd.DataFrame(
        {
            "transaction_id": [f"T{i}" for i in range(5)],
            "date": dates,
            "year_month": ["2024-01", "2024-01", "2024-01", "2024-02", "2024-02"],
            "amount": [5000.0, -100.0, -200.0, 5000.0, -50.0],
            "category": ["Salary", "Groceries", "Rent", "Salary", "Dining"],
            "type": ["income", "expense", "expense", "income", "expense"],
        }
    )


def test_monthly_summary_totals() -> None:
    monthly = build_monthly_summary(_transactions())
    assert len(monthly) == 2
    jan = monthly.loc[monthly["year_month"] == "2024-01"].iloc[0]
    assert jan["income"] == 5000.0
    assert jan["expenses"] == -300.0
    assert jan["net_cash_flow"] == 4700.0
    assert jan["txn_count"] == 3


def test_monthly_summary_zero_income_ratio_is_nan() -> None:
    df = _transactions()
    df = df[df["amount"] < 0]  # expenses only
    monthly = build_monthly_summary(df)
    assert monthly["expense_ratio"].isna().all()
    assert pd.api.types.is_float_dtype(monthly["expense_ratio"])


def test_category_summary_shares_sum_to_one() -> None:
    cats = build_category_summary(_transactions())
    # Groceries 100 + Rent 200 + Dining 50 → all fit within default top_n
    assert set(cats["category"]) == {"Groceries", "Rent", "Dining"}
    assert cats["share"].sum() == pytest.approx(1.0)


def test_category_summary_other_bucket() -> None:
    cats = build_category_summary(_transactions(), top_n=1)
    # Rent (200) outranks Groceries (100); the rest folds into "Other".
    assert list(cats["category"])[0] == "Rent"
    assert "Other" in set(cats["category"])
    other = cats.loc[cats["category"] == "Other"].iloc[0]
    assert other["total"] == pytest.approx(150.0)  # Groceries 100 + Dining 50


def test_rolling_features_computes_mean() -> None:
    daily = add_rolling_features(_transactions())
    assert "rolling_30d_avg" in daily.columns
    # One txn per date: 5000, -100, -200, 5000, -50
    assert daily.iloc[0]["rolling_30d_avg"] == pytest.approx(5000.0)
    assert daily.iloc[1]["rolling_30d_avg"] == pytest.approx((5000.0 - 100.0) / 2)
