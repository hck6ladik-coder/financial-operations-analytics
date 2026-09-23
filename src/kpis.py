"""KPI definitions and calculations — all formulas documented."""

from __future__ import annotations

import logging
import math
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# KPI formulas (documented for README / data dictionary)
#
# cash_flow          = inflow − outflow          (per period)
# burn_rate          = avg monthly net outflow   (trailing N months, absolute)
# margin             = (inflow − outflow) / inflow
# expense_ratio      = |expenses| / income       (by category or total)
# runway_months      = current_balance / burn_rate
# mom_variance_pct   = (current − previous) / |previous|
# ---------------------------------------------------------------------------


def compute_kpis(
    monthly: pd.DataFrame,
    cfg: dict[str, Any],
    current_balance: float | None = None,
) -> dict[str, float]:
    """Compute headline KPIs from monthly summary.

    Returns a flat dict suitable for dashboard header and AI summary.
    """
    if monthly.empty:
        return {
            "total_income": 0.0,
            "total_expenses": 0.0,
            "net_cash_flow": 0.0,
            "burn_rate": 0.0,
            "margin": 0.0,
            "runway_months": 0.0,
            "mom_variance_pct": 0.0,
            "current_balance": 0.0,
        }

    total_income = float(monthly["income"].sum())
    total_expenses = float(monthly["expenses"].sum())  # already negative
    net = total_income + total_expenses

    n = cfg["kpis"]["burn_rate_trailing_months"]
    trailing = monthly.tail(n)
    # Burn rate = average monthly net outflow (positive number when net is negative)
    avg_net = float(trailing["net_cash_flow"].mean())
    burn_rate = abs(min(avg_net, 0.0))  # only count outflow periods

    margin = (net / total_income) if total_income else 0.0

    if current_balance is None:
        current_balance = float(cfg["kpis"]["start_balance"]) + net

    # Infinite runway when there is no burn (no outflow periods in the window).
    runway = current_balance / burn_rate if burn_rate > 0 else math.inf

    # MoM variance on net cash flow
    if len(monthly) >= 2:
        prev = monthly.iloc[-2]["net_cash_flow"]
        curr = monthly.iloc[-1]["net_cash_flow"]
        mom = ((curr - prev) / abs(prev)) if prev != 0 else 0.0
    else:
        mom = 0.0

    result = {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_cash_flow": round(net, 2),
        "burn_rate": round(burn_rate, 2),
        "margin": round(margin, 4),
        "runway_months": round(runway, 1),
        "mom_variance_pct": round(mom * 100, 2),
        "current_balance": round(current_balance, 2),
    }
    logger.info(
        "KPIs computed: net=%.2f, burn=%.2f, runway=%.1f", net, burn_rate, result["runway_months"]
    )
    return result


def add_mom_yoy(monthly: pd.DataFrame) -> pd.DataFrame:
    """Add MoM and YoY variance columns using shift (Python equivalent of LAG)."""
    out = monthly.copy()
    out["net_lag1"] = out["net_cash_flow"].shift(1)
    out["net_lag12"] = out["net_cash_flow"].shift(12)
    out["mom_var"] = out["net_cash_flow"] - out["net_lag1"]
    out["mom_var_pct"] = out["mom_var"] / out["net_lag1"].abs().replace(0, float("nan"))
    out["yoy_var"] = out["net_cash_flow"] - out["net_lag12"]
    out["yoy_var_pct"] = out["yoy_var"] / out["net_lag12"].abs().replace(0, float("nan"))
    return out
