"""Load and expose project configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load config.yaml from project root (or given path)."""
    cfg_path = path or (PROJECT_ROOT / "config.yaml")
    with cfg_path.open(encoding="utf-8") as f:
        return cast(dict[str, Any], yaml.safe_load(f))


def get_path(cfg: dict[str, Any], key: str) -> Path:
    """Resolve a configured relative path against project root."""
    rel = cast(str, cfg["paths"][key])
    return PROJECT_ROOT / rel
