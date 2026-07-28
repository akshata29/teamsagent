"""Health and settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.infra.settings import Settings, get_settings
from app.models.demo_models import SettingsView

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/settings", response_model=SettingsView)
async def settings_view(settings: Settings = Depends(get_settings)) -> SettingsView:
    return SettingsView(
        use_native_acl=settings.use_native_acl,
        use_deployed_agent=settings.use_deployed_agent,
        offline_mode=settings.offline_mode,
        azure_configured=settings.azure_configured,
        search_api_version=settings.search_api_version,
        foundry_agent_name=settings.foundry_agent_name,
        default_b_variant="b1",
    )
