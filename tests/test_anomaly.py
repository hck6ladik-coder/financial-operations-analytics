"""Tests for anomaly detection."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.anomaly import detect_anomalies


def _category_df(amounts: list[float], category: str = "Groceries") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "transaction_id": [f"T{i}" for i in range(len(amounts))],
            "date": pd.date_range("2024-01-01", periods=len(amounts), freq="D"),
            "amount": amounts,
            "category": [category] * len(amounts),
            "type": ["expense"] * len(amounts),
        }
    )


def test_iqr_flags_outlier(cfg: dict[str, Any]) -> None:
    rng = np.random.default_rng(42)
    amounts = list(rng.normal(-50, 10, 30)) + [-500.0]  # clear outlier
    out = detect_anomalies(_category_df(amounts), cfg)
    assert out["is_anomaly"].sum() >= 1
    assert out.loc[out["amount"] == -500.0, "is_anomaly"].iloc[0]


def test_zscore_flags_outlier(cfg: dict[str, Any]) -> None:
    rng = np.random.default_rng(7)
    amounts = list(rng.normal(-50, 10, 50)) + [500.0]
    out = detect_anomalies(_category_df(amounts), cfg)
    row = out.loc[out["amount"] == 500.0].iloc[0]
    assert bool(row["is_anomaly"])
    assert "Zscore" in row["anomaly_reason"]


def test_small_category_not_flagged(cfg: dict[str, Any]) -> None:
    # min_category_size is 5 — smaller groups are skipped entirely
    out = detect_anomalies(_category_df([-10.0, -10.0, -9999.0]), cfg)
    assert out["is_anomaly"].sum() == 0


def test_reason_string_combined(cfg: dict[str, Any]) -> None:
    rng = np.random.default_rng(0)
    amounts = list(rng.normal(-50, 10, 40)) + [-800.0]
    out = detect_anomalies(_category_df(amounts), cfg)
    flagged = out.loc[out["is_anomaly"]]
    assert not flagged.empty
    assert flagged["anomaly_reason"].str.len().gt(0).all()
    assert not flagged["anomaly_reason"].str.endswith(";").any()
