"""Invoke the deployed Foundry hosted agent via the Responses API.

The hosted agent is invoked with ``agent_reference`` (the GA deployed-agent path).
For Option B (per-user), the trust-boundary layer has already retrieved the
user-trimmed documents; we inject them as grounding context in the request input.
For Option A, no grounding is injected — the agent's own in-container tool performs
the app-only Search.

Offline mode returns a deterministic synthesis from the supplied documents so the
demo runs without Azure.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence

from app.infra.settings import Settings, get_settings
from app.models.demo_models import DocHit

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are a Capital Markets research desk assistant. Answer using ONLY the provided "
    "research context. Cite document ids in square brackets. If the context is empty, say "
    "you have no entitled research for that query. All content is synthetic demo data."
)


def synthesize(
    query: str,
    grounding: Sequence[DocHit],
    settings: Optional[Settings] = None,
    inject_grounding: bool = True,
) -> str:
    """Return a grounded natural-language answer.

    ``inject_grounding=True`` (Option B) passes the pre-trimmed docs as context.
    ``inject_grounding=False`` (Option A) lets the deployed agent retrieve app-only.
    """
    settings = settings or get_settings()

    if not settings.use_deployed_agent or not settings.azure_configured:
        return _offline_answer(query, grounding)

    try:
        return _responses_answer(query, grounding, settings, inject_grounding)
    except Exception:  # noqa: BLE001 — never hard-fail the demo
        logger.exception("Deployed-agent invocation failed; using offline synthesis")
        return _offline_answer(query, grounding)


def _responses_answer(
    query: str,
    grounding: Sequence[DocHit],
    settings: Settings,
    inject_grounding: bool,
) -> str:
    from azure.identity import DefaultAzureCredential
    from azure.ai.projects import AIProjectClient

    project = AIProjectClient(
        endpoint=settings.foundry_project_endpoint,
        credential=DefaultAzureCredential(),
    )
    # Hosted agents MUST be called through their dedicated agent endpoint
    # (.../agents/<name>/endpoint/protocols/openai), not the shared responses
    # endpoint with agent_reference. get_openai_client(agent_name=...) targets it.
    client = project.get_openai_client(agent_name=settings.foundry_agent_name)

    if inject_grounding:
        context = "\n\n".join(f"[{d.id}] {d.title}\n{d.snippet}" for d in grounding)
        user_input = f"{_SYSTEM}\n\nContext:\n{context}\n\nQuestion: {query}"
    else:
        user_input = f"{_SYSTEM}\n\nQuestion: {query}"

    resp = client.responses.create(input=user_input)
    return getattr(resp, "output_text", "") or ""


def _offline_answer(query: str, grounding: Sequence[DocHit]) -> str:
    if not grounding:
        return (
            "No entitled research is available for your query under your current "
            "permissions. (Synthetic demo.)"
        )
    cited = ", ".join(f"[{d.id}]" for d in grounding)
    lead = grounding[0]
    return (
        f"Based on your entitled research {cited}: {lead.snippet} "
        f"\n\n(Synthetic demo synthesis for: \"{query}\".)"
    )


def as_ids(hits: List[DocHit]) -> List[str]:
    return [h.id for h in hits]
