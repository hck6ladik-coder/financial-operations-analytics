"""End-to-end orchestration: ingest → clean → validate → transform → export → report."""

from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path
from typing import Any

from src.anomaly import detect_anomalies
from src.clean import clean_transactions
from src.config import get_path, load_config
from src.export import export_all
from src.ingest import ingest_raw
from src.kpis import add_mom_yoy, compute_kpis
from src.logging_setup import setup_logging
from src.report import check_and_alert, write_report
from src.transform import build_category_summary, build_monthly_summary
from src.validate import validate_transactions

logger = logging.getLogger(__name__)


def run_pipeline(
    cfg: dict[str, Any] | None = None,
    source: Path | None = None,
    report_date: str | None = None,
) -> dict[str, Any]:
    """Execute the full pipeline and return key artefacts."""
    cfg = cfg or load_config()
    setup_logging(cfg)
    report_date = report_date or date.today().isoformat()

    logger.info("=== Pipeline start (date=%s) ===", report_date)

    # 1. Ingest
    raw = ingest_raw(cfg, source=source)

    # 2. Clean
    cleaned = clean_transactions(raw, cfg)

    # 3. Validate (fail-fast)
    validated = validate_transactions(cleaned, cfg)

    # 4. Anomaly detection
    enriched = detect_anomalies(validated, cfg)
    n_anomalies = int(enriched["is_anomaly"].sum())

    # 5. Transforms
    monthly = build_monthly_summary(enriched)
    monthly = add_mom_yoy(monthly)
    categories = build_category_summary(enriched, top_n=cfg["dashboard"]["top_n_categories"])
    kpis = compute_kpis(monthly, cfg)

    # 6. Persist processed
    processed_dir = get_path(cfg, "processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    proc_path = processed_dir / cfg["data"]["processed_filename"]
    enriched.to_parquet(proc_path, index=False)
    logger.info("Processed data -> %s", proc_path)

    # 7. Exports
    export_paths = export_all(enriched, monthly, categories, kpis, cfg)

    # 8. AI commentary
    commentary = _get_commentary(kpis, categories, n_anomalies, cfg)

    # 9. Report + alerts
    write_report(kpis, n_anomalies, commentary, cfg, report_date)
    check_and_alert(kpis, n_anomalies, cfg, report_date)

    logger.info("=== Pipeline complete ===")
    return {
        "kpis": kpis,
        "n_anomalies": n_anomalies,
        "commentary": commentary,
        "export_paths": {k: str(v) for k, v in export_paths.items()},
        "n_transactions": len(enriched),
    }


def _get_commentary(
    kpis: dict[str, float],
    categories: Any,
    n_anomalies: int,
    cfg: dict[str, Any],
) -> str:
    """Call AI layer with structured input; fall back to template."""
    try:
        from ai.summarize import summarize

        top_cats = (
            categories.head(3)[["category", "total", "share"]].to_dict("records")
            if hasattr(categories, "head")
            else []
        )
        payload = {
            "kpis": kpis,
            "top_categories": top_cats,
            "n_anomalies": n_anomalies,
        }
        return summarize(payload, cfg)
    except Exception as exc:
        logger.warning("AI layer unavailable (%s) - using fallback", exc)
        return (
            f"Net cash flow stands at {kpis.get('net_cash_flow', 0):,.0f} EUR. "
            f"Burn rate is {kpis.get('burn_rate', 0):,.0f} EUR/month giving "
            f"approximately {kpis.get('runway_months', 0):.1f} months of runway. "
            f"{n_anomalies} transactions were flagged as anomalous."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Financial Operations Analytics Pipeline")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Report date YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Optional path to an incoming transactions CSV",
    )
    args = parser.parse_args()
    source = Path(args.source) if args.source else None
    result = run_pipeline(source=source, report_date=args.date)
    print("\n[OK] Pipeline finished successfully")
    print(f"   Transactions : {result['n_transactions']}")
    print(f"   Net cash flow: {result['kpis']['net_cash_flow']:,.2f} EUR")
    print(f"   Anomalies    : {result['n_anomalies']}")
    print(f"   Commentary   : {result['commentary'][:120]}...")


if __name__ == "__main__":
    main()
