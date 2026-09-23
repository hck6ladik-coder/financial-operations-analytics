"""Optional Prefect flow illustrating orchestration.

Install prefect and run:
    pip install prefect
    prefect deploy flows/daily_ingest.py:daily_flow
"""

from __future__ import annotations

from pathlib import Path

try:
    from prefect import flow, task
except ImportError as exc:  # pragma: no cover - exercised only without prefect
    raise ImportError(
        "flows/daily_ingest.py requires the optional dependency 'prefect'. "
        "Install it with: pip install prefect"
    ) from exc


@task(retries=3, retry_delay_seconds=30)
def run_pipeline_task(source: str | None = None, report_date: str | None = None) -> dict:
    from src.pipeline import run_pipeline

    return run_pipeline(
        source=Path(source) if source else None,
        report_date=report_date,
    )


@flow(name="daily-financial-ingest")
def daily_flow(source: str | None = None, report_date: str | None = None) -> dict:
    """Daily ingest → validate → export → alert pipeline.

    Args:
        source: Optional path to incoming transactions CSV.
        report_date: Report date YYYY-MM-DD.

    Returns:
        Pipeline result dict with KPIs, anomalies, and commentary.
    """
    result = run_pipeline_task(source=source, report_date=report_date)
    return result


if __name__ == "__main__":
    result = daily_flow()
    print(result["kpis"])
