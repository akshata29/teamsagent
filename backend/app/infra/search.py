"""Azure AI Search client factories.

Two client shapes are needed:

* App-only client — authenticated with the app/managed identity (used by Option A).
* Per-user query — the same client but the query carries the end-user OBO token in
  the ``x-ms-query-source-authorization`` header (Option B native ACL trimming,
  API version ``2026-05-01-preview``).
"""

from __future__ import annotations

import logging
from typing import Optional

from app.infra.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def get_search_client(settings: Optional[Settings] = None):
    """Return an ``azure.search.documents.SearchClient`` using the app identity.

    Raises ImportError/exceptions to the caller if the SDK/credentials are missing;
    callers running in offline mode should not invoke this.
    """
    settings = settings or get_settings()
    from azure.search.documents import SearchClient

    if settings.search_key:
        # Admin/query key auth (no RBAC role needed). Preferred for local/demo runs.
        from azure.core.credentials import AzureKeyCredential

        credential = AzureKeyCredential(settings.search_key)
    else:
        from azure.identity import DefaultAzureCredential

        credential = DefaultAzureCredential()

    return SearchClient(
        endpoint=settings.search_endpoint,
        index_name=settings.search_index_name,
        credential=credential,
        api_version=settings.search_api_version,
    )
