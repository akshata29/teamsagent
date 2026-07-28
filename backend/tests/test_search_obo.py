"""Per-persona document-level trimming and Option A vs B contrast."""

from __future__ import annotations

from app.services import invoke_service


def test_option_a_is_undifferentiated_and_excludes_mnpi():
    a = invoke_service.run_option_a("equity-research", "semiconductor outlook")
    # App-only: sees non-MNPI docs regardless of persona (over-shares FI desk notes).
    assert "FI-CR-014" in a.visible_doc_ids
    assert a.identity_basis.value == "app_only"
    assert "DEAL-MEMO-007" not in a.visible_doc_ids  # MNPI excluded from app identity


def test_option_b_trims_to_persona_entitlements():
    b = invoke_service.run_option_b("equity-research", "semiconductor outlook")
    assert b.identity_basis.value == "per_user_obo"
    # Equity analyst must NOT see fixed-income desk notes or MNPI.
    assert "FI-CR-014" not in b.visible_doc_ids
    assert "DEAL-MEMO-007" not in b.visible_doc_ids
    assert "EQ-RES-001" in b.visible_doc_ids


def test_compliance_sees_mnpi_under_option_b():
    b = invoke_service.run_option_b("compliance", "project falcon deal memo")
    assert "DEAL-MEMO-007" in b.visible_doc_ids


def test_compare_reports_over_shared_docs():
    result = invoke_service.compare("equity-research", "high yield energy credit")
    # Option A exposes FI credit notes that Option B trims for an equity analyst.
    assert set(result.difference_doc_ids)
    assert all(d not in result.option_b.visible_doc_ids for d in result.difference_doc_ids)


def test_fi_pm_does_not_see_equity_notes_under_option_b():
    b = invoke_service.run_option_b("fi-pm", "high yield energy credit")
    assert "EQ-RES-001" not in b.visible_doc_ids
    assert "FI-CR-014" in b.visible_doc_ids
