#!/usr/bin/env python3
"""Remove generated artefacts (cross-platform replacement for shell one-liners)."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Globs relative to the project root; .gitkeep files are preserved.
ARTIFACT_GLOBS = (
    "data/processed/*",
    "data/exports/*",
    "data/interim/*",
    "reports/*.md",
    "reports/alerts/*",
)


def main() -> None:
    removed = 0
    for pattern in ARTIFACT_GLOBS:
        for path in ROOT.glob(pattern):
            if path.name == ".gitkeep":
                continue
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
            removed += 1

    cache_dirs = [p for p in ROOT.rglob("__pycache__") if p.is_dir()]
    for path in cache_dirs:
        shutil.rmtree(path, ignore_errors=True)
        removed += 1

    print(f"Cleaned {removed} generated artefact(s)")


if __name__ == "__main__":
    main()
