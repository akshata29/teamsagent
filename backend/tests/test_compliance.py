"""Compliance helpers: PII masking, token redaction, content-safety gate."""

from __future__ import annotations

from app.services import compliance


def test_mask_account_numbers():
    masked = compliance.mask_account_numbers("account 1234567890 flagged")
    assert "1234567890" not in masked
    assert masked.endswith("7890 flagged")


def test_redact_token_never_returns_token():
    assert compliance.redact_token("super-secret-token") == "***REDACTED***"


def test_is_safe_query_rejects_empty_and_oversized():
    assert compliance.is_safe_query("valid query")
    assert not compliance.is_safe_query("   ")
    assert not compliance.is_safe_query("x" * 1001)
