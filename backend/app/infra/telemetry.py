"""OpenTelemetry setup (no-op unless App Insights connection string is present)."""

from __future__ import annotations

import logging

from opentelemetry import trace

from app.infra.settings import get_settings

logger = logging.getLogger(__name__)


def setup_telemetry() -> None:
    settings = get_settings()
    if not settings.applicationinsights_connection_string:
        logger.info("Telemetry disabled (no APPLICATIONINSIGHTS_CONNECTION_STRING)")
        return
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            connection_string=settings.applicationinsights_connection_string
        )
        logger.info("Azure Monitor telemetry configured")
    except Exception:  # noqa: BLE001
        logger.exception("Failed to configure telemetry")


tracer = trace.get_tracer("capmarkets.demo")
