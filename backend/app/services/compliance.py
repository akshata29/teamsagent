"""PII / MNPI safety helpers.

For a financial-services demo we never log full user tokens, and we mask
account-number-style digit runs in any text that is logged. Content-safety checks
on user input are applied at the router boundary.
"""

from __future__ import annotations

import re

_ACCOUNT_RE = re.compile(r"\b(\d{6,})\b")


def mask_account_numbers(text: str) -> str:
    """Mask long digit runs (e.g. account numbers) to the last 4 digits."""

    def _mask(match: re.Match[str]) -> str:
        digits = match.group(1)
        return "*" * (len(digits) - 4) + digits[-4:]

    return _ACCOUNT_RE.sub(_mask, text)


def redact_token(_token: str) -> str:
    """Never log a token. Always return a fixed redaction marker."""
    return "***REDACTED***"


def is_safe_query(query: str) -> bool:
    """Minimal content-safety gate for the demo.

    Rejects empty/oversized input. A production build would call Azure AI Content
    Safety here before passing user text to an agent.
    """
    stripped = query.strip()
    return 0 < len(stripped) <= 1000
