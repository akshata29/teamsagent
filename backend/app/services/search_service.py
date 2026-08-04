"""Document-level-secure retrieval over the Capital Markets index.

Two retrieval modes model the Option A vs Option B contrast:

* ``app_only_search`` — Option A. Runs with the app/agent identity and returns an
  *undifferentiated* slice (everything except MNPI). It ignores the calling user,
  which is exactly the limitation of the direct-publish path: the Teams user token
  never reaches the tool, so results cannot be trimmed per user.

* ``per_user_search`` — Option B. Trims to the caller's entitlements. Live, it sends
  the OBO user token in ``x-ms-query-source-authorization`` (native ACL, preview)
  or falls back to GA security trimming with ``group_ids/any(search.in(...))``.

Offline mode uses the synthetic corpus so the whole demo runs without Azure.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from app.infra.settings import Settings, get_settings
from app.models.demo_models import Classification, DocHit

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from deploy.synthetic_data import (  # noqa: E402
    GRP_ALL,
    SYNTHETIC_DOCS,
    docs_for_groups,
)

_TOP_K = 5
_SELECT = ["id", "title", "content", "classification"]


def _rank(query: str, docs: list[dict]) -> list[dict]:
    """Naive keyword ranking for OFFLINE mode so query terms surface relevant docs."""
    terms = {t for t in query.lower().split() if len(t) > 2}

    def score(doc: dict) -> int:
        blob = f"{doc.get('title', '')} {doc.get('content', '')}".lower()
        return sum(blob.count(t) for t in terms)

    return sorted(docs, key=score, reverse=True)


def _to_hit(doc: dict, score: Optional[float] = None) -> DocHit:
    content = str(doc.get("content", ""))
    return DocHit(
        id=str(doc["id"]),
        title=str(doc["title"]),
        classification=Classification(str(doc.get("classification", "internal"))),
        snippet=content[:200],
        score=score,
    )


# --------------------------------------------------------------------------- #
# Option A — app-only (undifferentiated / admin app identity)
# --------------------------------------------------------------------------- #
def _admin_search_token(settings: Settings) -> Optional[str]:
    """Return an Azure AI Search token for the app/admin identity, or None.

    Uses ``DefaultAzureCredential`` — locally the signed-in dev identity, in a
    deployment the backend's managed identity. Presented to Search's ACL so the
    app-only path can retrieve as a full-access admin (Option A).
    """
    try:
        from azure.identity import DefaultAzureCredential

        return DefaultAzureCredential().get_token(settings.search_obo_scope).token
    except Exception:  # noqa: BLE001 — fall back to filter-only app-only search
        logger.warning("Admin search token unavailable; Option A falls back to non-MNPI filter")
        return None


def app_only_search(query: str, settings: Optional[Settings] = None) -> List[DocHit]:
    settings = settings or get_settings()
    if not settings.azure_configured:
        # Offline: an admin app identity sees the FULL corpus (incl. MNPI); otherwise the
        # legacy "everyone sees the same non-MNPI slice" story.
        if settings.option_a_admin_identity:
            candidates = list(SYNTHETIC_DOCS)
        else:
            candidates = [
                d for d in SYNTHETIC_DOCS if d.get("classification") != Classification.MNPI.value
            ]
        return [_to_hit(d) for d in _rank(query, candidates)][:_TOP_K]

    client = _live_client(settings)
    kwargs: dict = {"search_text": query, "select": _SELECT, "top": _TOP_K}
    admin_token = _admin_search_token(settings) if settings.option_a_admin_identity else None
    if admin_token:
        # Admin app identity: present its token to the ACL — full entitlements, no filter.
        kwargs["x_ms_query_source_authorization"] = admin_token
    else:
        # Fallback: undifferentiated non-MNPI slice.
        kwargs["filter"] = "classification ne 'mnpi'"
    results = client.search(**kwargs)
    return [_to_hit(dict(r), r.get("@search.score")) for r in results]


# --------------------------------------------------------------------------- #
# Option B — per-user (document-level trimming)
# --------------------------------------------------------------------------- #
def per_user_search(
    query: str,
    group_ids: Sequence[str],
    user_search_token: str,
    settings: Optional[Settings] = None,
) -> List[DocHit]:
    settings = settings or get_settings()
    if not settings.azure_configured:
        # Offline: trim the synthetic corpus to the caller's groups.
        return [_to_hit(d) for d in _rank(query, docs_for_groups(list(group_ids)))][:_TOP_K]

    client = _live_client(settings)
    kwargs: dict = {"search_text": query, "select": _SELECT, "top": _TOP_K}

    if settings.use_native_acl and user_search_token:
        # Native ACL trimming — Search resolves the user's groups from the OBO token.
        kwargs["x_ms_query_source_authorization"] = user_search_token
    else:
        # GA security trimming (also the fail-closed path when no user token is present):
        # we supply the resolved group IDs ourselves; empty groups => public (GRP_ALL) only.
        gids = ",".join([*group_ids, GRP_ALL])
        kwargs["filter"] = f"group_ids/any(g: search.in(g, '{gids}'))"

    results = client.search(**kwargs)
    return [_to_hit(dict(r), r.get("@search.score")) for r in results]


def _live_client(settings: Settings):
    from app.infra.search import get_search_client

    return get_search_client(settings)


def all_doc_ids() -> List[str]:
    """Every doc id in the corpus (used to compute trimmed-away sets)."""
    return [str(d["id"]) for d in SYNTHETIC_DOCS]


def catalog() -> List[DocHit]:
    """Title + classification for every doc (no content) — powers the UI visualizer."""
    return [
        DocHit(
            id=str(d["id"]),
            title=str(d["title"]),
            classification=Classification(str(d.get("classification", "internal"))),
            snippet="",
            entitled_to=_entitled_personas(d),
        )
        for d in SYNTHETIC_DOCS
    ]


def _entitled_personas(doc: dict) -> List[str]:
    """Human-readable labels for who is entitled to a document (for the access map).

    Derives from the doc's ``group_ids``/``user_ids`` against the persona registry:
    a persona is listed when its Entra principal appears on the document, and public
    docs (``GRP_ALL``) are labelled "Everyone".
    """
    from app.services import persona_service

    principals = set(doc.get("group_ids", [])) | set(doc.get("user_ids", []))
    labels = [
        f"{p.display_name} ({p.role})"
        for p in persona_service.list_personas()
        if p.entra_group_id in principals
    ]
    if GRP_ALL in doc.get("group_ids", []):
        labels = ["Everyone", *labels]
    return labels

