"""In-container Azure AI Search tool for the hosted agent (Option A path).

IMPORTANT: this tool runs INSIDE the Foundry hosted-agent container. The hosting
gateway strips the ``Authorization`` and all credential headers before the request
reaches the container, so the end-user's token is NOT available here. This tool can
therefore only query Search with the app / project managed identity (app-only).

Per-user document-level trimming is done in the trust-boundary layer (the Agents
SDK proxy / backend), not here — see the backend ``search_service`` /
``retrieval_service``.
"""

from __future__ import annotations

import logging
import os
from typing import List

from agent_framework import tool

logger = logging.getLogger(__name__)


@tool
def search_capital_markets_docs(query: str) -> List[dict]:
    """Retrieve Capital Markets research relevant to the query (app-only identity).

    Returns a list of {id, title, content, classification}. Excludes MNPI, which the
    app identity is not entitled to.
    """
    from azure.identity import DefaultAzureCredential
    from azure.search.documents import SearchClient

    endpoint = os.environ["SEARCH_ENDPOINT"]
    index = os.environ.get("SEARCH_INDEX_NAME", "capmarkets-research")
    api_version = os.environ.get("SEARCH_API_VERSION", "2026-05-01-preview")

    client = SearchClient(
        endpoint=endpoint,
        index_name=index,
        credential=DefaultAzureCredential(),
        api_version=api_version,
    )
    results = client.search(
        search_text=query,
        filter="classification ne 'mnpi'",
        select=["id", "title", "content", "classification"],
        top=5,
    )
    return [dict(r) for r in results]
