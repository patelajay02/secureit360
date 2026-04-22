"""Governance mapper for the Universal SaaS Connector.

Converts technical findings into director-level briefings that name the
regulation being touched. Every statement uses the template:

    "[plain-English finding]. Under [regulation], this creates [specific
     risk]. Recommended action: [clear next step]."

Country codes: NZ, AU, IN, AE. Unknown codes fall back to NZ.
"""

from typing import Any


# ── Regulation reference libraries per country ──────────────────────────────

REGULATIONS: dict[str, list[str]] = {
    "NZ": [
        "NZ Privacy Act 2020",
        "NZISM",
    ],
    "AU": [
        "Australian Privacy Act 1988",
        "ASD Essential Eight",
        "APRA CPS 234",
    ],
    "IN": [
        "DPDP Act 2023",
        "CERT-In Directive",
        "RBI Cyber Security Framework",
    ],
    "AE": [
        "UAE Federal PDPL 2021",
        "NESA IAS",
        "ADHICS",
        "DIFC / ADGM Data Protection",
    ],
}


# ── Per-check governance narrative. The {country_reg} token is filled in
# with the user's country-specific regulation name. ─────────────────────────

CHECK_NARRATIVES: dict[str, dict[str, str]] = {
    "admin_ratio": {
        "plain": (
            "More than a fifth of the workforce holds administrative access "
            "to this SaaS platform."
        ),
        "risk": (
            "an unnecessarily broad attack surface — a single compromised "
            "account could alter data, create new admins, or exfiltrate "
            "records the regulator deems personal information"
        ),
    },
    "mfa_coverage": {
        "plain": (
            "One or more accounts on this SaaS platform are not protected "
            "by multi-factor authentication."
        ),
        "risk": (
            "a direct control failure — a single phished or reused password "
            "is enough to take over the account, and the director is "
            "expected to have reasonable security safeguards in place"
        ),
    },
    "dormant_users": {
        "plain": (
            "Accounts that have not been used for more than 90 days are "
            "still active on this SaaS platform."
        ),
        "risk": (
            "an unnecessary attack surface and a record-keeping failure — "
            "former staff or stale accounts should be deprovisioned as part "
            "of a documented offboarding process"
        ),
    },
    "public_sharing": {
        "plain": (
            "One or more files or resources are shared publicly on the "
            "internet from this SaaS platform."
        ),
        "risk": (
            "an unauthorised disclosure risk — personal or commercially "
            "sensitive information may be retrievable by anyone with the "
            "link, which is a notifiable event under privacy law"
        ),
    },
    "audit_log_enabled": {
        "plain": (
            "Audit logging is not enabled on this SaaS platform."
        ),
        "risk": (
            "a detection and accountability gap — without logs the "
            "organisation cannot answer who did what during an incident, "
            "which undermines both breach investigation and regulator reporting"
        ),
    },
}


def _resolve_country(country: str | None) -> str:
    if not country:
        return "NZ"
    c = country.upper()
    return c if c in REGULATIONS else "NZ"


def map_to_governance(finding: dict[str, Any], country: str) -> dict[str, Any]:
    """Return a copy of the finding with governance_statement and
    regulation_refs populated for the given country.
    """
    c = _resolve_country(country)
    regs = REGULATIONS[c]
    narrative = CHECK_NARRATIVES.get(finding.get("check_id", ""), {
        "plain": finding.get("technical_detail") or "A security control gap was identified.",
        "risk": "a governance gap that the director is expected to address",
    })

    primary_reg = regs[0]
    recommended = finding.get("recommended_action") or "Review and remediate."

    governance_statement = (
        f"{narrative['plain']} "
        f"Under {primary_reg}, this creates {narrative['risk']}. "
        f"Recommended action: {recommended}"
    )

    mapped = dict(finding)
    mapped["governance_statement"] = governance_statement
    mapped["regulation_refs"] = regs
    return mapped
