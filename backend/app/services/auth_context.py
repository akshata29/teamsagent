"""Per-request user authentication context for per-user (Option B) retrieval.

The same backend serves two front doors, and both resolve to one of these:

* SPA sign-in (MSAL.js) — the browser sends ``Authorization: Bearer <user token>``
  issued for THIS backend's API scope. The backend performs the On-Behalf-Of
  exchange for the Azure AI Search scope. ``user_assertion`` carries that token.

* Teams proxy (Custom Engine Agent) — the proxy already performed the OBO exchange
  and forwards the Search-scoped token in ``x-ms-query-source-authorization``.
  ``search_token`` carries that already-exchanged token.

Either way the downstream per-user Search call is identical, so the same deployed
agent works whether surfaced in the web UI or in Teams.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UserAuth:
    """Resolved per-request user credentials for downstream Search."""

    # Already-exchanged Azure AI Search token (Teams proxy path).
    search_token: str = ""
    # User assertion issued for this backend's API scope (SPA path) — needs OBO.
    user_assertion: str = ""

    @property
    def has_user(self) -> bool:
        return bool(self.search_token or self.user_assertion)


def from_headers(
    authorization: Optional[str],
    x_ms_query_source_authorization: Optional[str],
) -> UserAuth:
    """Build a :class:`UserAuth` from the relevant inbound request headers."""
    bearer = ""
    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            bearer = parts[1].strip()
    return UserAuth(
        search_token=(x_ms_query_source_authorization or "").strip(),
        user_assertion=bearer,
    )
