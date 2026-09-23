"""Tests for the FastAPI / Vercel entrypoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_index_serves_html() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Plotly" in resp.text


def test_health() -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_summary_returns_kpis_and_commentary() -> None:
    resp = client.get("/api/summary")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["n_transactions"] > 0
    assert "net_cash_flow" in payload["kpis"]
    assert payload["commentary"]
    # response must be strict JSON (no bare Infinity tokens)
    assert "Infinity" not in resp.text


def test_monthly_endpoint() -> None:
    rows = client.get("/api/monthly").json()
    assert rows
    assert {"year_month", "income", "expenses", "net_cash_flow"} <= set(rows[0])


def test_categories_endpoint() -> None:
    rows = client.get("/api/categories").json()
    assert rows
    assert {"category", "total", "share"} <= set(rows[0])


def test_anomalies_endpoint_flagged_only() -> None:
    rows = client.get("/api/anomalies").json()
    assert rows
    assert {"transaction_id", "amount", "anomaly_reason"} <= set(rows[0])
