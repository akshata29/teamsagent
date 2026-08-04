"""Synthetic Capital Markets research corpus for the demo.

ALL CONTENT IS SYNTHETIC and for demonstration only — no real market data, no real
MNPI. Document-level security is modeled via Entra USER object-IDs on each document,
demonstrating an information barrier between the Equity Research and Fixed-Income desks
and a full-control Compliance/Admin user.

The user OIDs here MUST match `backend/app/services/persona_service.py`.
"""

from __future__ import annotations

from typing import Dict, List

# --- Canonical Entra principals (all three are USER object-IDs in this tenant) ---
# IMPORTANT: these are USER OIDs, NOT group GUIDs. AI Search native ACL matches a
# signed-in user's OID against the index ``UserIds`` field, so each user's OID must
# live in the docs' ``user_ids`` (never ``group_ids``). Verified live via `az ad user`.
USER_FABRIC_A = "1d3ff50d-4dc5-4a8d-8074-b92731dc2bd8"  # fabricusera@ — Equity Research desk
USER_FABRIC_B = "ec5f7a00-b2fc-4650-bdc8-01f2d718ea6c"  # fabricuserb@ — Fixed-Income desk
USER_ADMIN = "91a5dd7e-5b13-41f8-aea1-d7ecaed5760c"     # admin@ — Compliance, full control
# Special value understood by AI Search native ACLs / demo trimming: visible to everyone.
GRP_ALL = "all"


# Each doc: id, title, classification, content, group_ids (entitled groups),
# user_ids (entitled individual users). Desk entitlements are modeled per-USER (their
# OID in user_ids). The full-control Admin user is added to user_ids of every non-public
# doc so that identity sees everything. Only the public disclaimer uses group_ids (GRP_ALL).
SYNTHETIC_DOCS: List[Dict[str, object]] = [
    {
        "id": "EQ-RES-001",
        "title": "Semiconductor sector overweight thesis (SYNTHETIC)",
        "classification": "internal",
        "content": (
            "SYNTHETIC RESEARCH. We move the semiconductor sub-sector to overweight on "
            "accelerating AI-accelerator demand and easing inventory. Preferred names screen "
            "well on FCF yield and design-win momentum. Key risk: export-control headlines."
        ),
        "group_ids": [],
        "user_ids": [USER_FABRIC_A, USER_ADMIN],
    },
    {
        "id": "EQ-RES-002",
        "title": "Consumer staples defensive rotation note (SYNTHETIC)",
        "classification": "internal",
        "content": (
            "SYNTHETIC RESEARCH. With rates volatility elevated, we highlight defensive "
            "staples with pricing power and stable gross margins as a lower-beta ballast."
        ),
        "group_ids": [],
        "user_ids": [USER_FABRIC_A, USER_ADMIN],
    },
    {
        "id": "FI-CR-014",
        "title": "High-yield energy credit note (SYNTHETIC)",
        "classification": "internal",
        "content": (
            "SYNTHETIC RESEARCH. Selective add in single-B energy credits where coverage "
            "ratios and hedged production support spread tightening; avoid weakest refiners."
        ),
        "group_ids": [],
        "user_ids": [USER_FABRIC_B, USER_ADMIN],
    },
    {
        "id": "FI-CR-021",
        "title": "Investment-grade financials curve positioning (SYNTHETIC)",
        "classification": "internal",
        "content": (
            "SYNTHETIC RESEARCH. Prefer the belly of the IG financials curve; new-issue "
            "concessions have normalized and dispersion favors up-in-quality carry."
        ),
        "group_ids": [],
        "user_ids": [USER_FABRIC_B, USER_ADMIN],
    },
    {
        "id": "RATES-STRAT-003",
        "title": "Duration positioning and curve steepeners (SYNTHETIC)",
        "classification": "internal",
        "content": (
            "SYNTHETIC RESEARCH. We favor modest long duration via 5s30s steepeners into "
            "the next data cycle; term premium looks rich to fair-value models."
        ),
        "group_ids": [],
        "user_ids": [USER_FABRIC_A, USER_FABRIC_B, USER_ADMIN],
    },
    {
        "id": "DEAL-MEMO-007",
        "title": "Project Falcon M&A deal memo — MNPI (SYNTHETIC)",
        "classification": "mnpi",
        "content": (
            "SYNTHETIC MNPI — COMPLIANCE ONLY. Draft memo re: potential acquisition of a "
            "mid-cap industrial target ('Project Falcon'). Contains material non-public "
            "information behind the information barrier. Not for research or trading desks."
        ),
        "group_ids": [],
        "user_ids": [USER_ADMIN],
    },
    {
        "id": "SURV-021",
        "title": "Trade-surveillance exception report — Compliance only (SYNTHETIC)",
        "classification": "mnpi",
        "content": (
            "SYNTHETIC — COMPLIANCE ONLY. Weekly surveillance exceptions: three flagged "
            "cross-desk information-barrier near-misses under review. Restricted distribution."
        ),
        "group_ids": [],
        "user_ids": [USER_ADMIN],
    },
    {
        "id": "DISC-000",
        "title": "Research disclaimer and distribution policy (SYNTHETIC)",
        "classification": "public",
        "content": (
            "SYNTHETIC PUBLIC. Standard research disclaimer: past performance is not "
            "indicative of future results; this material is for information only and is not "
            "investment advice. MiFID II research-unbundling policy applies."
        ),
        "group_ids": [GRP_ALL],
        "user_ids": [],
    },
]


def docs_for_groups(principals: List[str]) -> List[Dict[str, object]]:
    """Return docs visible to any of the given principals (groups or user OIDs, or GRP_ALL)."""
    wanted = set(principals) | {GRP_ALL}
    return [
        d
        for d in SYNTHETIC_DOCS
        if wanted & (set(d["group_ids"]) | set(d.get("user_ids", [])))  # type: ignore[arg-type]
    ]
