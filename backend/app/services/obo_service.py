"""On-Behalf-Of token exchange for downstream Azure AI Search access.

Exchanges the calling user's token (the "user assertion") for a token scoped to
Azure AI Search (`https://search.azure.com/.default`). This is the trust-boundary
step for Option B per-user document-level security. In OFFLINE mode no real
exchange happens and a demo marker token is returned.
"""

from __future__ import annotations

import logging

from app.infra.settings import Settings, get_settings

logger = logging.getLogger(__name__)

# Prefix of the fabricated persona assertion produced by
# ``persona_service.mock_user_assertion`` for offline/no-SSO surfaces (e.g. the
# Agents Playground, which has no real Teams SSO). Such a token is never a real
# Entra JWT, so a live OBO exchange on it is guaranteed to fail with AADSTS50027.
_DEMO_ASSERTION_PREFIX = "demo-user-assertion::"


class OboError(RuntimeError):
    """Raised when an OBO exchange cannot be completed."""


def exchange_for_search_token(user_assertion: str, settings: Settings | None = None) -> str:
    """Return a Search-scoped access token for the user behind `user_assertion`.

    Uses ``azure.identity.OnBehalfOfCredential``. Requires the app registration to
    have the delegated Azure AI Search permission with admin consent.
    """
    settings = settings or get_settings()

    if settings.offline_mode or not settings.aad_client_id:
        logger.info("OBO exchange skipped (offline/demo mode)")
        return f"demo-search-token::{user_assertion}"

    # No real Teams SSO (Playground / no-SSO surface): the caller handed us the
    # fabricated persona assertion. Skip the live exchange — it would always fail
    # AADSTS50027 — and fail closed to public-only without a noisy stack trace.
    if user_assertion.startswith(_DEMO_ASSERTION_PREFIX):
        logger.info("OBO skipped: no real user token (no-SSO surface); failing closed to public-only")
        raise OboError("No real user token to exchange (no-SSO surface)")

    try:
        from azure.identity import OnBehalfOfCredential

        credential = OnBehalfOfCredential(
            tenant_id=settings.aad_tenant_id,
            client_id=settings.aad_client_id,
            client_secret=settings.aad_client_secret,
            user_assertion=user_assertion,
        )
        token = credential.get_token(settings.search_obo_scope)
        return token.token
    except Exception as exc:  # noqa: BLE001 — surface as a domain error, never leak token
        logger.exception("OBO exchange failed")
        raise OboError("Failed to exchange user token for Azure AI Search") from exc
