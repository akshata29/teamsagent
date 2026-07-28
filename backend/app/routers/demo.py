"""Demo endpoints: personas, Option A / Option B invocation, compare, audit.

Content-safety is enforced at this boundary (compliance.is_safe_query) before any
user text reaches an agent. Every invocation is audited inside the service layer.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException, status

from app.models.demo_models import (
    AuditRecord,
    CompareResult,
    DocHit,
    InvokeRequest,
    InvokeResult,
    Persona,
)
from app.services import audit_service, compliance, invoke_service, persona_service, search_service
from app.services.auth_context import from_headers

router = APIRouter(prefix="/demo")


def _validate(req: InvokeRequest) -> None:
    if not compliance.is_safe_query(req.query):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UNSAFE_QUERY", "message": "Query failed the content-safety check"},
        )
    if persona_service.get_persona(req.persona_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PERSONA_NOT_FOUND", "message": f"Unknown persona {req.persona_id}"},
        )


@router.get("/personas", response_model=List[Persona])
async def personas() -> List[Persona]:
    return persona_service.list_personas()


@router.get("/corpus", response_model=List[DocHit])
async def corpus() -> List[DocHit]:
    """Catalog of all research documents (titles only) for the trim visualizer."""
    return search_service.catalog()


@router.post("/optionA/invoke", response_model=InvokeResult)
async def option_a(req: InvokeRequest) -> InvokeResult:
    _validate(req)
    return invoke_service.run_option_a(req.persona_id, req.query)


@router.post("/optionB/invoke", response_model=InvokeResult)
async def option_b(
    req: InvokeRequest,
    authorization: Optional[str] = Header(default=None),
    x_ms_query_source_authorization: Optional[str] = Header(default=None),
) -> InvokeResult:
    _validate(req)
    auth = from_headers(authorization, x_ms_query_source_authorization)
    return invoke_service.run_option_b(req.persona_id, req.query, req.variant, auth=auth)


@router.post("/compare", response_model=CompareResult)
async def compare(
    req: InvokeRequest,
    authorization: Optional[str] = Header(default=None),
    x_ms_query_source_authorization: Optional[str] = Header(default=None),
) -> CompareResult:
    _validate(req)
    auth = from_headers(authorization, x_ms_query_source_authorization)
    return invoke_service.compare(req.persona_id, req.query, req.variant, auth=auth)


@router.get("/audit", response_model=List[AuditRecord])
async def audit(limit: int = 50) -> List[AuditRecord]:
    return audit_service.recent(limit)
