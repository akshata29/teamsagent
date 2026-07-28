"""Application configuration via pydantic-settings.

Loads from an absolute `.env` path so the settings resolve regardless of the
current working directory when uvicorn is launched. `get_settings()` is cached.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from typing_extensions import Annotated
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# backend/app/infra/settings.py -> backend/.env
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    """Effective configuration for the demo backend."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Microsoft Foundry ---
    foundry_project_endpoint: str = ""
    foundry_agent_name: str = "capmarkets-research-agent"
    foundry_model_deployment: str = "gpt-4o"

    # --- Azure AI Search ---
    search_endpoint: str = ""
    search_index_name: str = "capmarkets-research"
    search_api_version: str = "2026-05-01-preview"
    search_key: str = ""

    # --- Entra ID / OBO ---
    aad_tenant_id: str = ""
    aad_client_id: str = ""
    aad_client_secret: str = ""
    search_obo_scope: str = "https://search.azure.com/.default"

    # --- Azure OpenAI (embeddings) ---
    aoai_endpoint: str = ""
    aoai_api_version: str = "2024-12-01-preview"
    aoai_embed_deployment: str = "text-embedding-3-small"
    aoai_embed_dims: int = 1536

    # --- Teams publish (Option A) ---
    bot_service_arm_id: str = ""
    publish_scope: str = "Tenant"

    # --- Feature flags ---
    use_native_acl: bool = True
    use_deployed_agent: bool = True
    offline_mode: bool = False
    # Option A: treat the app / managed identity as a full-access admin, so its app-only
    # Search returns the entire corpus (incl. MNPI) instead of an empty/undifferentiated
    # slice. Locally the admin identity is the signed-in dev identity; in a real deploy it
    # is the backend's managed identity granted full entitlements on the index.
    option_a_admin_identity: bool = True

    # --- CORS ---
    cors_origins: Annotated[List[str], NoDecode] = ["http://localhost:5173"]

    # --- Observability ---
    applicationinsights_connection_string: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors(cls, v: object) -> object:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def azure_configured(self) -> bool:
        """True when the core Azure endpoints are present (not offline)."""
        return bool(self.search_endpoint and self.foundry_project_endpoint) and not self.offline_mode


@lru_cache
def get_settings() -> Settings:
    return Settings()
