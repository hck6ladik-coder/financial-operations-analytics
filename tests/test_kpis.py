"""Tests for KPI calculations."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd
import pytest

from src.kpis import add_mom_yoy, compute_kpis


def test_compute_kpis_basic(cfg: dict[str, Any]) -> None:
    monthly = pd.DataFrame(
        {
            "year_month": ["2024-01", "2024-02", "2024-03"],
            "income": [5000.0, 5100.0, 5200.0],
            "expenses": [-3000.0, -3100.0, -3200.0],
            "net_cash_flow": [2000.0, 2000.0, 2000.0],
        }
    )
    kpis = compute_kpis(monthly, cfg)
    assert kpis["total_income"] == 15300.0
    assert kpis["total_expenses"] == -9300.0
    assert kpis["net_cash_flow"] == 6000.0
    assert kpis["burn_rate"] == 0.0  # positive net → no burn
    assert kpis["margin"] == pytest.approx(6000 / 15300, rel=1e-3)


def test_burn_rate_when_negative(cfg: dict[str, Any]) -> None:
    monthly = pd.DataFrame(
        {
            "year_month": ["2024-01", "2024-02", "2024-03"],
            "income": [1000.0, 1000.0, 1000.0],
            "expenses": [-2000.0, -2000.0, -2000.0],
            "net_cash_flow": [-1000.0, -1000.0, -1000.0],
        }
    )
    kpis = compute_kpis(monthly, cfg)
    assert kpis["burn_rate"] == 1000.0
    # runway = balance / burn (finite when burn > 0)
    assert math.isfinite(kpis["runway_months"])


def test_runway_infinite_without_burn(cfg: dict[str, Any]) -> None:
    monthly = pd.DataFrame(
        {
            "year_month": ["2024-01"],
            "income": [5000.0],
            "expenses": [-1000.0],
            "net_cash_flow": [4000.0],
        }
    )
    kpis = compute_kpis(monthly, cfg)
    assert kpis["burn_rate"] == 0.0
    assert math.isinf(kpis["runway_months"])


def test_empty_monthly_same_keys_as_populated(cfg: dict[str, Any]) -> None:
    empty = pd.DataFrame(columns=["year_month", "income", "expenses", "net_cash_flow"])
    populated = pd.DataFrame(
        {
            "year_month": ["2024-01"],
            "income": [100.0],
            "expenses": [-50.0],
            "net_cash_flow": [50.0],
        }
    )
    assert set(compute_kpis(empty, cfg)) == set(compute_kpis(populated, cfg))


def test_add_mom_yoy_lags() -> None:
    monthly = pd.DataFrame(
        {
            "year_month": [f"2024-{m:02d}" for m in range(1, 14)],
            "net_cash_flow": [float(i) for i in range(1, 14)],
        }
    )
    out = add_mom_yoy(monthly)
    assert out["net_lag1"].isna().sum() == 1
    assert out["net_lag12"].isna().sum() == 12
    assert out.loc[1, "mom_var"] == 1.0
    assert out.loc[12, "yoy_var"] == 12.0
