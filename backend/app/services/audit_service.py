"""Append-only audit trail for demo invocations.

Every invocation logs who asked, under which persona/group, which option, and which
documents were visible vs trimmed. Tokens are NEVER written. Records are appended to
an in-memory ring (for the UI) and to a JSONL file next to the backend.
"""

from __future__ import annotations

import json
import logging
from collections import deque
from pathlib import Path
from typing import Deque, List

from app.models.demo_models import AuditRecord

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_AUDIT_FILE = _BACKEND_ROOT / "audit_log.jsonl"
_RING: Deque[AuditRecord] = deque(maxlen=200)


def record(entry: AuditRecord) -> None:
    """Persist an audit record (memory ring + JSONL append)."""
    _RING.append(entry)
    try:
        with _AUDIT_FILE.open("a", encoding="utf-8") as fh:
            fh.write(entry.model_dump_json() + "\n")
    except OSError:
        logger.exception("Failed to append audit record to %s", _AUDIT_FILE)


def recent(limit: int = 50) -> List[AuditRecord]:
    """Return the most recent audit records (newest first)."""
    items = list(_RING)[-limit:]
    return list(reversed(items))
