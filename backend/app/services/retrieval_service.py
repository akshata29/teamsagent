"""Option B2 — per-user retrieval kept inside the model run via the Responses API.

This demonstrates the *closest-to-in-agent* per-user path from the research: a
trusted proxy calls ``responses.create`` with the Azure AI Search knowledge-base
MCP tool passed INLINE, carrying the end-user's search-scoped OBO token in the
tool's ``headers["x-ms-query-source-authorization"]``. The model orchestrates the
retrieval and synthesis server-side, trimmed per user.

Constraints (see research [S7]): Preview (2026-05-01-preview); this is a Responses
call with the tool defined inline — NOT a deployed-agent ``agent_reference`` call.
Offline mode falls back to proxy-side retrieval + local synthesis.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence

from app.infra.settings import Settings, get_settings
from app.models.demo_models import DocHit
from app.services import foundry_service, search_service

logger = logging.getLogger(__name__)


def inline_mcp_answer(
    query: str,
    group_ids: Sequence[str],
    user_search_token: str,
    settings: Optional[Settings] = None,
) -> tuple[str, List[DocHit]]:
    """Return (answer, doc_hits) using the inline AI Search KB MCP tool (B2).

    Offline / not-configured: fall back to B1-style proxy retrieval + local synthesis
    so the demo still shows per-user trimming.
    """
    settings = settings or get_settings()
    hits = search_service.per_user_search(query, group_ids, user_search_token, settings)

    if not settings.azure_configured:
        answer = foundry_service.synthesize(query, hits, settings, inject_grounding=True)
        return answer, hits

    try:
        answer = _responses_inline_mcp(query, user_search_token, settings)
        return answer, hits
    except Exception:  # noqa: BLE001
        logger.exception("Inline-MCP Responses call failed; using proxy retrieval synthesis")
        answer = foundry_service.synthesize(query, hits, settings, inject_grounding=True)
        return answer, hits


def _responses_inline_mcp(query: str, user_search_token: str, settings: Settings) -> str:
    from azure.identity import DefaultAzureCredential
    from azure.ai.projects import AIProjectClient

    project = AIProjectClient(
        endpoint=settings.foundry_project_endpoint,
        credential=DefaultAzureCredential(),
    )
    client = project.get_openai_client()

    # Inline AI Search knowledge-base MCP tool carrying the per-request user token.
    tools = [
        {
            "type": "mcp",
            "server_label": "capmarkets-search",
            "server_url": f"{settings.search_endpoint}/agents/knowledge/mcp",
            "headers": {"x-ms-query-source-authorization": user_search_token},
        }
    ]
    resp = client.responses.create(
        model=settings.foundry_model_deployment,
        input=query,
        tools=tools,
    )
    return getattr(resp, "output_text", "") or ""
