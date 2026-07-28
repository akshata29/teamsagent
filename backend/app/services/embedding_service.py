"""Query embeddings via Azure OpenAI, with an offline deterministic fallback."""

from __future__ import annotations

import hashlib
import logging
from typing import List, Optional

from app.infra.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def embed(text: str, settings: Optional[Settings] = None) -> List[float]:
    """Return an embedding vector for `text`.

    Live: Azure OpenAI embeddings deployment. Offline/demo: a deterministic
    pseudo-vector derived from a hash so the demo runs without Azure OpenAI.
    """
    settings = settings or get_settings()

    if settings.offline_mode or not settings.aoai_endpoint:
        return _deterministic_vector(text, settings.aoai_embed_dims)

    try:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        from openai import AzureOpenAI

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )
        client = AzureOpenAI(
            azure_endpoint=settings.aoai_endpoint,
            azure_ad_token_provider=token_provider,
            api_version=settings.aoai_api_version,
        )
        resp = client.embeddings.create(model=settings.aoai_embed_deployment, input=text)
        return resp.data[0].embedding
    except Exception:  # noqa: BLE001 — fall back so the demo never hard-fails
        logger.exception("Embedding call failed; using deterministic fallback")
        return _deterministic_vector(text, settings.aoai_embed_dims)


def _deterministic_vector(text: str, dims: int) -> List[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    # Tile the 32-byte digest out to `dims` and scale to [-1, 1].
    return [((digest[i % len(digest)] / 255.0) * 2.0 - 1.0) for i in range(dims)]
