"""Standardised logging configuration."""

from __future__ import annotations

import logging
import sys
from typing import Any


def setup_logging(cfg: dict[str, Any] | None = None) -> None:
    """Configure root logger from config or sensible defaults."""
    level_name = "INFO"
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    if cfg and "logging" in cfg:
        level_name = cfg["logging"].get("level", level_name)
        fmt = cfg["logging"].get("format", fmt)

    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
