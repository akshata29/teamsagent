"""Orchestration for the three demo invocation paths (Option A, B1, B2).

Keeps routers thin: this module wires OBO exchange, retrieval, and agent synthesis,
computes the visible/trimmed document sets, and writes the audit record.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Optional

from app.infra.settings import Settings, get_settings
from app.models.demo_models import (
    AuditRecord,
    CompareResult,
    DemoOption,
    DocHit,
    IdentityBasis,
    InvokeResult,
    Persona,
)
from app.services import (
    audit_service,
    foundry_service,
    obo_service,
    persona_service,
    retrieval_service,
    search_service,
)
from app.services.auth_context import UserAuth

logger = logging.getLogger(__name__)


class PersonaNotFound(LookupError):
    """Raised when an unknown persona id is supplied."""


def _visible_trimmed(hits: list[DocHit]) -> tuple[list[str], list[str]]:
    visible = [h.id for h in hits]
    trimmed = [d for d in search_service.all_doc_ids() if d not in visible]
    return visible, trimmed


def _audit(result: InvokeResult, persona: Persona) -> None:
    audit_service.record(
        AuditRecord(
            persona_id=persona.id,
            entra_group_id=persona.entra_group_id,
            option=result.option,
            query=result.query,
            visible_doc_ids=result.visible_doc_ids,
            trimmed_doc_ids=result.trimmed_doc_ids,
            identity_basis=result.identity_basis,
            trace_id=result.trace_id,
        )
    )


def run_option_a(persona_id: str, query: str, settings: Optional[Settings] = None) -> InvokeResult:
    """Option A — deployed hosted agent, app-only in-container Search (no per-user trimming)."""
    settings = settings or get_settings()
    persona = _require_persona(persona_id)
    start = time.perf_counter()
    trace_id = uuid.uuid4().hex

    hits = search_service.app_only_search(query, settings)
    # Option A runs with the app/admin identity (no per-user OBO). When that identity is
    # treated as a full-access admin, ground the answer on what it retrieved so the agent
    # reflects the admin view instead of returning "no entitled research".
    inject = settings.option_a_admin_identity
    answer = foundry_service.synthesize(query, hits, settings, inject_grounding=inject)
    visible, trimmed = _visible_trimmed(hits)

    result = InvokeResult(
        option=DemoOption.A,
        persona_id=persona.id,
        query=query,
        answer=answer,
        doc_hits=hits,
        visible_doc_ids=visible,
        trimmed_doc_ids=trimmed,
        identity_basis=IdentityBasis.APP_ONLY,
        latency_ms=int((time.perf_counter() - start) * 1000),
        trace_id=trace_id,
        note=(
            "Direct publish: no per-user OBO. The app/managed identity is treated as an "
            "admin with full entitlements, so Search returns the entire corpus (incl. MNPI) "
            "— everyone sees the same full slice, regardless of who is asking."
        ),
    )
    _audit(result, persona)
    return result


def run_option_b(
    persona_id: str,
    query: str,
    variant: Optional[str] = None,
    settings: Optional[Settings] = None,
    auth: Optional[UserAuth] = None,
) -> InvokeResult:
    """Option B — trust-boundary OBO; per-user document-level trimming."""
    settings = settings or get_settings()
    persona = _require_persona(persona_id)
    variant = (variant or "b1").lower()
    start = time.perf_counter()
    trace_id = uuid.uuid4().hex

    # Resolve the per-user Search token. Priority:
    #   1. A real token supplied on the request — either an already-exchanged Search
    #      token from the Teams proxy, or a Bearer user token from the SPA that we
    #      exchange here via OBO. This is the SAME agent whether surfaced in the web
    #      UI or in Teams.
    #   2. Offline/demo fallback: a mock persona assertion (offline returns a marker).
    try:
        search_token = _resolve_search_token(persona, auth, settings)
        identity_basis = IdentityBasis.PER_USER_OBO
    except obo_service.OboError:
        # Fail-closed: without a user token, only public documents are returned.
        logger.warning("OBO unavailable; failing closed to public-only")
        search_token = ""
        identity_basis = IdentityBasis.PUBLIC_ONLY

    if identity_basis == IdentityBasis.PUBLIC_ONLY:
        hits = search_service.per_user_search(query, [], search_token, settings)
        answer = foundry_service.synthesize(query, hits, settings, inject_grounding=True)
        option = DemoOption.B1
    elif variant == "b2":
        answer, hits = retrieval_service.inline_mcp_answer(
            query, [persona.entra_group_id], search_token, settings
        )
        option = DemoOption.B2
    else:
        hits = search_service.per_user_search(
            query, [persona.entra_group_id], search_token, settings
        )
        answer = foundry_service.synthesize(query, hits, settings, inject_grounding=True)
        option = DemoOption.B1

    visible, trimmed = _visible_trimmed(hits)
    note = (
        "Agents SDK proxy is the trust boundary: Teams SSO -> OBO -> AI Search trimmed "
        "per user, then grounding injected into the hosted agent."
    )
    if option == DemoOption.B2:
        note = (
            "Inline AI Search KB MCP tool on a Responses call carries the per-request user "
            "token (x-ms-query-source-authorization) — retrieval trimmed inside the model run."
        )
    if identity_basis == IdentityBasis.PUBLIC_ONLY:
        note = "OBO unavailable — failed closed to public-only documents."

    result = InvokeResult(
        option=option,
        persona_id=persona.id,
        query=query,
        answer=answer,
        doc_hits=hits,
        visible_doc_ids=visible,
        trimmed_doc_ids=trimmed,
        identity_basis=identity_basis,
        latency_ms=int((time.perf_counter() - start) * 1000),
        trace_id=trace_id,
        note=note,
    )
    _audit(result, persona)
    return result


def compare(
    persona_id: str,
    query: str,
    variant: Optional[str] = None,
    settings: Optional[Settings] = None,
    auth: Optional[UserAuth] = None,
) -> CompareResult:
    """Run Option A and Option B for the same persona + query and diff the doc sets."""
    settings = settings or get_settings()
    option_a = run_option_a(persona_id, query, settings)
    option_b = run_option_b(persona_id, query, variant, settings, auth)
    # Docs Option A exposed that Option B trimmed away for this persona.
    difference = [d for d in option_a.visible_doc_ids if d not in option_b.visible_doc_ids]
    return CompareResult(
        persona_id=persona_id,
        query=query,
        option_a=option_a,
        option_b=option_b,
        difference_doc_ids=difference,
    )


def _require_persona(persona_id: str) -> Persona:
    persona = persona_service.get_persona(persona_id)
    if persona is None:
        raise PersonaNotFound(persona_id)
    return persona


def _resolve_search_token(
    persona: Persona, auth: Optional[UserAuth], settings: Settings
) -> str:
    """Return an Azure AI Search token for the calling user.

    * Teams proxy already exchanged it — use ``auth.search_token`` directly.
    * SPA sent a Bearer user token — exchange it for the Search scope via OBO.
    * No real token — fall back to the mock persona assertion (offline returns a
      marker token; a live OBO on a mock assertion raises and fails closed).
    """
    if auth and auth.search_token:
        return auth.search_token
    if auth and auth.user_assertion:
        return obo_service.exchange_for_search_token(auth.user_assertion, settings)
    assertion = persona_service.mock_user_assertion(persona.id)
    return obo_service.exchange_for_search_token(assertion, settings)
