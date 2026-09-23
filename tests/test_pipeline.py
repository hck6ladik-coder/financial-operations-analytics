"""End-to-end pipeline tests — all outputs redirected to a temp directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.config import load_config
from src.pipeline import run_pipeline


@pytest.fixture
def tmp_cfg(tmp_path: Path) -> dict[str, Any]:
    cfg = load_config()
    for key in ("interim", "processed", "exports", "reports", "alerts", "incoming"):
        cfg["paths"][key] = str(tmp_path / key)
    return cfg


def test_pipeline_end_to_end(tmp_cfg: dict[str, Any]) -> None:
    result = run_pipeline(cfg=tmp_cfg, report_date="2024-06-01")

    assert result["n_transactions"] > 0
    assert result["commentary"]
    assert Path(result["export_paths"]["kpis"]).exists()

    reports_dir = Path(tmp_cfg["paths"]["reports"])
    assert (reports_dir / "report_2024-06-01.md").exists()

    processed = Path(tmp_cfg["paths"]["processed"]) / tmp_cfg["data"]["processed_filename"]
    assert processed.exists()


def test_pipeline_writes_alert_for_sample_data(tmp_cfg: dict[str, Any]) -> None:
    # Sample data breaches the anomaly-count threshold (32 > 5).
    result = run_pipeline(cfg=tmp_cfg, report_date="2024-06-02")

    alert_path = Path(tmp_cfg["paths"]["alerts"]) / "2024-06-02.json"
    assert alert_path.exists()

    payload = json.loads(alert_path.read_text(encoding="utf-8"))
    assert payload["reasons"]
    assert payload["n_anomalies"] == result["n_anomalies"]
    assert payload["kpis"]["net_cash_flow"] == result["kpis"]["net_cash_flow"]


def test_pipeline_accepts_custom_source(tmp_cfg: dict[str, Any], tmp_path: Path) -> None:
    raw = load_config()
    source = tmp_path / "incoming_sample.csv"
    head = pd.read_csv(Path(raw["paths"]["raw"]) / raw["data"]["raw_filename"]).head(20)
    head.to_csv(source, index=False)

    result = run_pipeline(cfg=tmp_cfg, source=source, report_date="2024-06-03")
    assert result["n_transactions"] == len(head)
