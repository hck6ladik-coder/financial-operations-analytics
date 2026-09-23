"""Anomaly detection: IQR (default), Z-score, optional Isolation Forest."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def flag_iqr(df: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    """Flag amounts outside [Q1 − k·IQR, Q3 + k·IQR] per category."""
    k = cfg["anomaly"]["iqr_multiplier"]
    min_size = cfg["anomaly"]["min_category_size"]
    out = df.copy()
    out["anomaly_iqr"] = False
    out["anomaly_reason"] = ""

    for cat, grp in out.groupby("category"):
        if len(grp) < min_size:
            continue
        q1 = grp["amount"].quantile(0.25)
        q3 = grp["amount"].quantile(0.75)
        iqr = q3 - q1
        low = q1 - k * iqr
        high = q3 + k * iqr
        mask = (out["category"] == cat) & ((out["amount"] < low) | (out["amount"] > high))
        out.loc[mask, "anomaly_iqr"] = True
        out.loc[mask, "anomaly_reason"] = out.loc[mask, "anomaly_reason"] + f"IQR({cat});"

    n = int(out["anomaly_iqr"].sum())
    logger.info("IQR anomalies flagged: %d", n)
    return out


def flag_zscore(df: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    """Flag |z| > threshold per category."""
    thr = cfg["anomaly"]["zscore_threshold"]
    min_size = cfg["anomaly"]["min_category_size"]
    out = df.copy()
    if "anomaly_zscore" not in out.columns:
        out["anomaly_zscore"] = False
    if "anomaly_reason" not in out.columns:
        out["anomaly_reason"] = ""

    for cat, grp in out.groupby("category"):
        if len(grp) < min_size:
            continue
        mu = grp["amount"].mean()
        sigma = grp["amount"].std(ddof=0)
        if sigma == 0 or np.isnan(sigma):
            continue
        z = (out.loc[out["category"] == cat, "amount"] - mu) / sigma
        mask_idx = z[z.abs() > thr].index
        out.loc[mask_idx, "anomaly_zscore"] = True
        out.loc[mask_idx, "anomaly_reason"] = (
            out.loc[mask_idx, "anomaly_reason"] + f"Zscore({cat});"
        )

    n = int(out["anomaly_zscore"].sum())
    logger.info("Z-score anomalies flagged: %d", n)
    return out


def detect_anomalies(df: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    """Run IQR + Z-score; combine into single is_anomaly flag."""
    out = flag_iqr(df, cfg)
    out = flag_zscore(out, cfg)
    out["is_anomaly"] = out["anomaly_iqr"] | out["anomaly_zscore"]
    out["anomaly_reason"] = out["anomaly_reason"].str.rstrip(";")
    n = int(out["is_anomaly"].sum())
    logger.info("Total anomalies: %d (%.1f%%)", n, 100 * n / len(out) if len(out) else 0)
    return out
