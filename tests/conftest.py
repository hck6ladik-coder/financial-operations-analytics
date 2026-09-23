"""Shared pytest fixtures."""

from __future__ import annotations

from typing import Any

import pytest

from src.config import load_config


@pytest.fixture
def cfg() -> dict[str, Any]:
    return load_config()
