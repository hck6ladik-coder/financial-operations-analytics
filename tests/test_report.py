"""Tests for report generation and alert thresholds."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest

from src.config import load_config
from src.report import check_and_alert, write_report


@pytest.fixture
def report_cfg(tmp_path: Path) -> dict[str, Any]:
    cfg = load_config()
    cfg["paths"]["reports"] = str(tmp_path / "reports")
    cfg["paths"]["alerts"] = str(tmp_path / "alerts")
    return cfg


KPIS: dict[str, float] = {
    "total_income": 10000.0,
    "total_expenses": -4000.0,
    "net_cash_flow": 6000.0,
    "burn_rate": 0.0,
    "margin": 0.6,
    "runway_months": math.inf,
    "mom_variance_pct": 5.0,
    "current_balance": 21000.0,
}


def test_write_report_contains_kpis_and_commentary(report_cfg: dict[str, Any]) -> None:
    path = write_report(KPIS, 3, "Some commentary.", report_cfg, "2024-05-01")
    text = path.read_text(encoding="utf-8")
    assert "6,000.00 EUR" in text
    assert "Some commentary." in text
    assert "inf" in text  # infinite runway rendered as 'inf'


def test_no_alert_below_thresholds(report_cfg: dict[str, Any]) -> None:
    kpis = {**KPIS, "mom_variance_pct": 5.0}
    assert check_and_alert(kpis, 3, report_cfg, "2024-05-02") is None
    assert not (Path(report_cfg["paths"]["alerts"]) / "2024-05-02.json").exists()


def test_alert_on_anomaly_count(report_cfg: dict[str, Any]) -> None:
    path = check_and_alert(KPIS, 12, report_cfg, "2024-05-03")
    assert path is not None
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert any("Anomaly count" in r for r in payload["reasons"])


def test_alert_on_mom_deviation(report_cfg: dict[str, Any]) -> None:
    kpis = {**KPIS, "mom_variance_pct": -42.0}
    path = check_and_alert(kpis, 1, report_cfg, "2024-05-04")
    assert path is not None
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert any("MoM" in r for r in payload["reasons"])


def test_alert_json_is_valid_with_infinite_runway(report_cfg: dict[str, Any]) -> None:
    path = check_and_alert(KPIS, 12, report_cfg, "2024-05-05")
    assert path is not None
    payload = json.loads(path.read_text(encoding="utf-8"))  # would raise on Infinity
    assert payload["kpis"]["runway_months"] is None
