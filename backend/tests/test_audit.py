"""Audit trail behavior."""

from __future__ import annotations

from app.models.demo_models import AuditRecord, DemoOption, IdentityBasis
from app.services import audit_service, invoke_service


def test_record_and_recent():
    entry = AuditRecord(
        persona_id="compliance",
        entra_group_id="33333333-3333-3333-3333-333333333333",
        option=DemoOption.B1,
        query="test",
        visible_doc_ids=["DISC-000"],
        trimmed_doc_ids=[],
        identity_basis=IdentityBasis.PER_USER_OBO,
    )
    audit_service.record(entry)
    recent = audit_service.recent(5)
    assert recent[0].persona_id == "compliance"


def test_invocation_writes_audit():
    before = len(audit_service.recent(200))
    invoke_service.run_option_a("equity-research", "semiconductor")
    after = len(audit_service.recent(200))
    assert after >= before + 1
