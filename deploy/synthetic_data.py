"""Synthetic Capital Markets research corpus for the demo.

ALL CONTENT IS SYNTHETIC and for demonstration only — no real market data, no real
MNPI. Document-level security is modeled via Entra group GUIDs on each document,
demonstrating an information barrier between Equity Research, Fixed-Income, and
Compliance desks.

The group GUIDs here MUST match `backend/app/services/persona_service.py`.
"""

from __future__ import annotations

from typing import Dict, List

# --- Canonical Entra principals ---
# Equity Research and Fixed-Income are real Entra security GROUPS (matched via GroupIds).
GRP_EQUITY_RESEARCH = "1d3ff50d-4dc5-4a8d-8074-b92731dc2bd8"
GRP_FI_PM = "ec5f7a00-b2fc-4650-bdc8-01f2d718ea6c"
# Compliance is granted at the USER level (full control) via this Entra object-ID
# (matched via UserIds). This user sees every document, including MNPI.
GRP_COMPLIANCE = "91a5dd7e-5b13-41f8-aea1-d7ecaed5760c"
# Special value understood by AI Search native ACLs / demo trimming: visible to everyone.
GRP_ALL = "all"


# Each doc: id, title, classification, content, group_ids (entitled groups),
# user_ids (entitled individual users). The full-control Compliance user is added to
# user_ids of every non-public doc so that identity sees everything.
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
        "group_ids": [GRP_EQUITY_RESEARCH],
        "user_ids": [GRP_COMPLIANCE],
    },
    {
        "id": "EQ-RES-002",
        "title": "Consumer staples defensive rotation note (SYNTHETIC)",
        "classification": "internal",
        "content": (
            "SYNTHETIC RESEARCH. With rates volatility elevated, we highlight defensive "
            "staples with pricing power and stable gross margins as a lower-beta ballast."
        ),
        "group_ids": [GRP_EQUITY_RESEARCH],
        "user_ids": [GRP_COMPLIANCE],
    },
    {
        "id": "FI-CR-014",
        "title": "High-yield energy credit note (SYNTHETIC)",
        "classification": "internal",
        "content": (
            "SYNTHETIC RESEARCH. Selective add in single-B energy credits where coverage "
            "ratios and hedged production support spread tightening; avoid weakest refiners."
        ),
        "group_ids": [GRP_FI_PM],
        "user_ids": [GRP_COMPLIANCE],
    },
    {
        "id": "FI-CR-021",
        "title": "Investment-grade financials curve positioning (SYNTHETIC)",
        "classification": "internal",
        "content": (
            "SYNTHETIC RESEARCH. Prefer the belly of the IG financials curve; new-issue "
            "concessions have normalized and dispersion favors up-in-quality carry."
        ),
        "group_ids": [GRP_FI_PM],
        "user_ids": [GRP_COMPLIANCE],
    },
    {
        "id": "RATES-STRAT-003",
        "title": "Duration positioning and curve steepeners (SYNTHETIC)",
        "classification": "internal",
        "content": (
            "SYNTHETIC RESEARCH. We favor modest long duration via 5s30s steepeners into "
            "the next data cycle; term premium looks rich to fair-value models."
        ),
        "group_ids": [GRP_FI_PM, GRP_EQUITY_RESEARCH],
        "user_ids": [GRP_COMPLIANCE],
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
        "user_ids": [GRP_COMPLIANCE],
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
        "user_ids": [GRP_COMPLIANCE],
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
