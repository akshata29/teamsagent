"""Persona registry for the Capital Markets demo.

Personas map to synthetic Entra groups defined in `deploy/synthetic_data.py`
(single source of truth for the group GUIDs). Each persona also produces a mock
user assertion used only in OFFLINE demo mode (never a real token).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

from app.models.demo_models import Persona

# Make the repo-root `deploy` package importable so the group GUIDs stay single-source.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from deploy.synthetic_data import (  # noqa: E402
    USER_ADMIN,
    USER_FABRIC_A,
    USER_FABRIC_B,
)

_PERSONAS: Dict[str, Persona] = {
    "equity-research": Persona(
        id="equity-research",
        display_name="Fabric User A",
        role="Equity Research desk",
        entra_group_id=USER_FABRIC_A,
        entitlement_summary="Equity research notes and public commentary. No MNPI, no fixed-income desk.",
    ),
    "fi-pm": Persona(
        id="fi-pm",
        display_name="Fabric User B",
        role="Fixed-Income desk",
        entra_group_id=USER_FABRIC_B,
        entitlement_summary="Credit / rates research and public commentary. No MNPI, no equity desk notes.",
    ),
    "compliance": Persona(
        id="compliance",
        display_name="Admin",
        role="Compliance (full control)",
        entra_group_id=USER_ADMIN,
        entitlement_summary="Full access incl. MNPI deal memos and surveillance reports (behind the barrier).",
    ),
}


def list_personas() -> List[Persona]:
    return list(_PERSONAS.values())


def get_persona(persona_id: str) -> Optional[Persona]:
    return _PERSONAS.get(persona_id)


def mock_user_assertion(persona_id: str) -> str:
    """A stand-in 'user assertion' for OFFLINE mode only.

    In a live deployment this is the real Teams-user access token obtained via SSO
    and exchanged with OBO — never fabricated. Here it is an opaque demo string.
    """
    return f"demo-user-assertion::{persona_id}"
