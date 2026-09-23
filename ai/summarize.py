"""Purposeful AI layer: turn structured analytics into ≤120-word commentary.

Contract
--------
Input  : dict with keys
         - kpis: dict[str, float]
         - top_categories: list[dict]  (category, total, share)
         - n_anomalies: int
Output : str  (≤ max_words words)

If no external LLM is configured, a deterministic template is used.
Never sends raw PII or transaction-level data.
"""

from __future__ import annotations

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)


def summarize(payload: dict[str, Any], cfg: dict[str, Any] | None = None) -> str:
    """Produce a short natural-language summary for a financial specialist."""
    max_words = 120
    if cfg and "ai" in cfg:
        max_words = cfg["ai"].get("max_words", 120)
        if not cfg["ai"].get("enabled", True):
            return _fallback(payload)

    # In this simulation we always use the deterministic fallback.
    # A real deployment could call an LLM here with the structured payload only.
    text = _fallback(payload)
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words]) + "…"
    return text


def _fallback(payload: dict[str, Any]) -> str:
    """Deterministic template — always available, no external dependency."""
    kpis = payload.get("kpis", {})
    n_anom = payload.get("n_anomalies", 0)
    top = payload.get("top_categories", [])

    income = kpis.get("total_income", 0)
    expenses = kpis.get("total_expenses", 0)
    net = kpis.get("net_cash_flow", 0)
    burn = kpis.get("burn_rate", 0)
    runway = kpis.get("runway_months", 0)
    mom = kpis.get("mom_variance_pct", 0)
    margin = kpis.get("margin", 0) * 100

    cat_txt = ""
    if top:
        parts = [f"{c.get('category', '?')} ({c.get('share', 0) * 100:.0f}%)" for c in top[:3]]
        cat_txt = " Largest expense shares: " + ", ".join(parts) + "."

    direction = "improved" if mom > 0 else "deteriorated" if mom < 0 else "was stable"
    anom_txt = (
        f" {n_anom} transactions were flagged as anomalous and warrant review."
        if n_anom
        else " No material anomalies were detected."
    )

    return (
        f"Over the analysed period, total income reached {income:,.0f} EUR against "
        f"expenses of {expenses:,.0f} EUR, producing a net cash flow of {net:,.0f} EUR "
        f"(margin {margin:.1f}%). Month-over-month net cash flow {direction} by "
        f"{abs(mom):.1f}%. The trailing burn rate sits at {burn:,.0f} EUR per month, "
        f"implying roughly {'inf' if not math.isfinite(runway) else f'{runway:.1f}'} months of runway at the current balance."
        f"{cat_txt}{anom_txt}"
    )
