"""Transform cleaned data into analysis-ready tables."""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def build_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate income, expenses, net cash flow by calendar month."""
    monthly = (
        df.groupby("year_month")
        .agg(
            income=("amount", lambda s: s[s > 0].sum()),
            expenses=("amount", lambda s: s[s < 0].sum()),
            txn_count=("transaction_id", "count"),
        )
        .reset_index()
    )
    monthly["net_cash_flow"] = monthly["income"] + monthly["expenses"]
    monthly["expense_ratio"] = monthly["expenses"].abs() / monthly["income"].replace(
        0, float("nan")
    )
    monthly = monthly.sort_values("year_month").reset_index(drop=True)
    logger.info("Built monthly summary: %d periods", len(monthly))
    return monthly


def build_category_summary(df: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    """Expense totals by category with share and top-N + Other."""
    exp = df[df["amount"] < 0].copy()
    cat = (
        exp.groupby("category")
        .agg(total=("amount", "sum"), txn_count=("transaction_id", "count"))
        .reset_index()
    )
    cat["total"] = cat["total"].abs()
    cat = cat.sort_values("total", ascending=False).reset_index(drop=True)
    grand = cat["total"].sum()
    cat["share"] = cat["total"] / grand if grand else 0.0

    if len(cat) > top_n:
        top = cat.head(top_n)
        other = pd.DataFrame(
            {
                "category": ["Other"],
                "total": [cat.iloc[top_n:]["total"].sum()],
                "txn_count": [cat.iloc[top_n:]["txn_count"].sum()],
                "share": [cat.iloc[top_n:]["share"].sum()],
            }
        )
        cat = pd.concat([top, other], ignore_index=True)

    logger.info("Built category summary: %d categories", len(cat))
    return cat


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """Rolling mean of daily net over the last 30 recorded days (rows)."""
    daily = df.groupby("date").agg(daily_net=("amount", "sum")).reset_index().sort_values("date")
    daily["rolling_30d_avg"] = daily["daily_net"].rolling(window=30, min_periods=1).mean()
    return daily
