"""Tests for the AI commentary layer."""

from __future__ import annotations

import math
from typing import Any

from ai.summarize import summarize

PAYLOAD: dict[str, Any] = {
    "kpis": {
        "total_income": 275578.0,
        "total_expenses": -152433.0,
        "net_cash_flow": 123145.0,
        "burn_rate": 0.0,
        "margin": 0.447,
        "runway_months": math.inf,
        "mom_variance_pct": 3.2,
    },
    "top_categories": [
        {"category": "Transport", "total": 36000.0, "share": 0.24},
        {"category": "Groceries", "total": 24000.0, "share": 0.16},
        {"category": "Dining", "total": 16000.0, "share": 0.11},
    ],
    "n_anomalies": 12,
}


def test_summary_within_word_limit(cfg: dict[str, Any]) -> None:
    text = summarize(PAYLOAD, cfg)
    assert 0 < len(text.split()) <= cfg["ai"]["max_words"]


def test_summary_mentions_key_figures() -> None:
    text = summarize(PAYLOAD, None)
    assert "123,145" in text
    assert "Transport" in text
    assert "12 transactions" in text
    assert "inf" in text


def test_summary_without_anomalies() -> None:
    payload = {**PAYLOAD, "n_anomalies": 0}
    text = summarize(payload, None)
    assert "No material anomalies" in text


def test_disabled_ai_still_returns_fallback(cfg: dict[str, Any]) -> None:
    cfg["ai"]["enabled"] = False
    text = summarize(PAYLOAD, cfg)
    assert text


def test_malformed_payload_does_not_crash() -> None:
    text = summarize({}, None)
    assert isinstance(text, str)
    assert text
