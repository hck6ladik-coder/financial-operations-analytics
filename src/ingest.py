"""Ingest raw CSV into the raw layer (no transformation)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import get_path

logger = logging.getLogger(__name__)


def ingest_raw(cfg: dict[str, Any], source: Path | None = None) -> pd.DataFrame:
    """Load the raw transactions CSV.

    Parameters
    ----------
    cfg : dict
        Project configuration.
    source : Path | None
        Optional override path (used by daily automation for incoming files).

    Returns
    -------
    pd.DataFrame
        Untouched raw data.
    """
    if source is None:
        source = get_path(cfg, "raw") / cfg["data"]["raw_filename"]

    if not source.exists():
        raise FileNotFoundError(
            f"Raw data not found at {source}. "
            "Run scripts/generate_synthetic_data.py or place a CSV in data/raw/."
        )

    df = pd.read_csv(source)
    logger.info("Ingested %d rows from %s", len(df), source)
    return df
