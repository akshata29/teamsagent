"""Pytest fixtures — force offline behavior and a clean settings cache."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _BACKEND_ROOT.parent
for p in (str(_BACKEND_ROOT), str(_REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("OFFLINE_MODE", "true")


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from app.infra.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
