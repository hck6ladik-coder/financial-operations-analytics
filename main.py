"""Vercel entrypoint — FastAPI app serving analytics JSON and a Plotly dashboard.

The Vercel filesystem is read-only, so analytics are computed in memory from
the committed raw CSV (no parquet/report files are written). Streamlit remains
available locally via `make dashboard`.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from ai.summarize import summarize
from src.anomaly import detect_anomalies
from src.clean import clean_transactions
from src.config import load_config
from src.ingest import ingest_raw
from src.kpis import add_mom_yoy, compute_kpis
from src.transform import build_category_summary, build_monthly_summary
from src.validate import validate_transactions

app = FastAPI(title="Financial Operations Analytics", version="1.0.0")

_HTML_PATH = Path(__file__).resolve().parent / "dashboard" / "web.html"

_ANOMALY_COLUMNS = [
    "date",
    "transaction_id",
    "category",
    "counterparty",
    "amount",
    "anomaly_reason",
]


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """JSON-safe records (dates ISO, NaN → null)."""
    records: list[dict[str, Any]] = json.loads(df.to_json(orient="records", date_format="iso"))
    return records


def _finite(values: dict[str, Any]) -> dict[str, Any]:
    """Replace non-finite floats with null so responses are valid JSON."""
    return {
        k: (None if isinstance(v, float) and not math.isfinite(v) else v) for k, v in values.items()
    }


@lru_cache(maxsize=1)
def _analytics() -> dict[str, Any]:
    """Run the read-only part of the pipeline once per cold start."""
    cfg = load_config()
    validated = validate_transactions(clean_transactions(ingest_raw(cfg), cfg), cfg)
    enriched = detect_anomalies(validated, cfg)

    monthly = add_mom_yoy(build_monthly_summary(enriched))
    categories = build_category_summary(enriched, top_n=cfg["dashboard"]["top_n_categories"])
    kpis = compute_kpis(monthly, cfg)

    n_anomalies = int(enriched["is_anomaly"].sum())
    top_cats = categories.head(3)[["category", "total", "share"]]
    commentary = summarize(
        {
            "kpis": kpis,
            "top_categories": json.loads(top_cats.to_json(orient="records")),
            "n_anomalies": n_anomalies,
        },
        cfg,
    )
    anomalies = enriched.loc[enriched["is_anomaly"], _ANOMALY_COLUMNS]

    return {
        "kpis": kpis,
        "n_transactions": len(enriched),
        "n_anomalies": n_anomalies,
        "commentary": commentary,
        "monthly": _records(monthly),
        "categories": _records(categories),
        "anomalies": _records(anomalies),
    }


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Plotly dashboard (static HTML + JSON APIs)."""
    return _HTML_PATH.read_text(encoding="utf-8")


@app.get("/api/summary")
def summary() -> dict[str, Any]:
    data = _analytics()
    return {
        "kpis": _finite(data["kpis"]),
        "n_transactions": data["n_transactions"],
        "n_anomalies": data["n_anomalies"],
        "commentary": data["commentary"],
    }


@app.get("/api/monthly")
def monthly_endpoint() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = _analytics()["monthly"]
    return rows


@app.get("/api/categories")
def categories_endpoint() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = _analytics()["categories"]
    return rows


@app.get("/api/anomalies")
def anomalies_endpoint() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = _analytics()["anomalies"]
    return rows


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
