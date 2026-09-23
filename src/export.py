"""Write dashboard-ready exports with stable schema."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import get_path

logger = logging.getLogger(__name__)


def export_all(
    transactions: pd.DataFrame,
    monthly: pd.DataFrame,
    categories: pd.DataFrame,
    kpis: dict[str, float],
    cfg: dict[str, Any],
) -> dict[str, Path]:
    """Persist Parquet/CSV exports and return written paths."""
    export_dir = get_path(cfg, "exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}

    # Transactions (with anomaly flags)
    txn_path = export_dir / "transactions.parquet"
    transactions.to_parquet(txn_path, index=False)
    paths["transactions"] = txn_path

    # Monthly
    mon_path = export_dir / "monthly_summary.parquet"
    monthly.to_parquet(mon_path, index=False)
    paths["monthly"] = mon_path

    # Categories
    cat_path = export_dir / "category_summary.parquet"
    categories.to_parquet(cat_path, index=False)
    paths["categories"] = cat_path

    # KPIs as single-row CSV for easy dashboard read
    kpi_path = export_dir / "kpis.csv"
    pd.DataFrame([kpis]).to_csv(kpi_path, index=False)
    paths["kpis"] = kpi_path

    # Also CSV copies for BI tools that prefer CSV
    transactions.to_csv(export_dir / "transactions.csv", index=False)
    monthly.to_csv(export_dir / "monthly_summary.csv", index=False)

    logger.info("Exports written to %s (%d files)", export_dir, len(paths))
    return paths
