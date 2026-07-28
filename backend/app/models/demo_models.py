"""Pydantic v2 models for the Capital Markets Teams-agent demo.

These are transport (request/response) and domain models only — no business logic.
Financial naming follows the domain glossary (client/analyst, research, classification).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DemoOption(str, Enum):
    """Which integration path produced a result."""

    A = "A"  # Direct Foundry publish — hosted agent, app-only Search
    B1 = "B1"  # Agents SDK proxy — proxy-side OBO retrieval + grounding injection
    B2 = "B2"  # Inline AI Search KB MCP tool on a Responses call (preview)


class IdentityBasis(str, Enum):
    """How AI Search results were trimmed for a given invocation."""

    APP_ONLY = "app_only"  # agent/app identity — undifferentiated slice (Option A)
    PER_USER_OBO = "per_user_obo"  # per-user OBO token — real document-level security
    PUBLIC_ONLY = "public_only"  # fail-closed fallback when OBO unavailable


class Classification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    MNPI = "mnpi"  # material non-public information — Compliance only


class Persona(BaseModel):
    """A Capital Markets user persona mapped to an Entra group entitlement."""

    id: str = Field(..., description="Stable persona key, e.g. 'equity-research'")
    display_name: str
    role: str
    entra_group_id: str = Field(..., description="Entra object-ID GUID (synthetic for demo)")
    entitlement_summary: str


class DocHit(BaseModel):
    """A single retrieved research document."""

    id: str
    title: str
    classification: Classification
    snippet: str = Field(default="", description="Short excerpt shown in the UI")
    score: Optional[float] = None


class InvokeRequest(BaseModel):
    """Run the agent for a persona under a given option."""

    persona_id: str = Field(..., description="Which persona is asking")
    query: str = Field(..., min_length=1, max_length=1000)
    variant: Optional[str] = Field(
        default=None,
        description="For Option B: 'b1' (proxy retrieve, default) or 'b2' (inline MCP)",
    )


class InvokeResult(BaseModel):
    """Result of a single option invocation."""

    option: DemoOption
    persona_id: str
    query: str
    answer: str
    doc_hits: List[DocHit] = Field(default_factory=list)
    visible_doc_ids: List[str] = Field(default_factory=list)
    trimmed_doc_ids: List[str] = Field(default_factory=list)
    identity_basis: IdentityBasis
    latency_ms: int = 0
    trace_id: Optional[str] = None
    note: Optional[str] = Field(default=None, description="Human-readable path explanation")


class CompareResult(BaseModel):
    """Side-by-side Option A vs Option B for the same query + persona."""

    persona_id: str
    query: str
    option_a: InvokeResult
    option_b: InvokeResult
    # Docs Option A returned that Option B trimmed away for this persona.
    difference_doc_ids: List[str] = Field(default_factory=list)


class AuditRecord(BaseModel):
    """Append-only audit trail entry for a demo invocation."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    persona_id: str
    entra_group_id: str
    option: DemoOption
    query: str
    visible_doc_ids: List[str] = Field(default_factory=list)
    trimmed_doc_ids: List[str] = Field(default_factory=list)
    identity_basis: IdentityBasis
    trace_id: Optional[str] = None


class SettingsView(BaseModel):
    """Non-secret effective settings surfaced to the UI."""

    use_native_acl: bool
    use_deployed_agent: bool
    offline_mode: bool
    azure_configured: bool
    search_api_version: str
    foundry_agent_name: str
    default_b_variant: str
