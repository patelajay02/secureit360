"""Generic reusable check library for the Universal SaaS Connector.

Each function takes a normalized payload and returns a list of findings.
A finding is a dict:
    {
        "check_id":           stable slug, e.g. "admin_ratio"
        "severity":           "critical" | "high" | "medium" | "low" | "info"
        "technical_detail":   what was observed (may name specific users)
        "recommended_action": clear next step
    }

Governance statements and regulation references are layered on later in
governance_mapper.py. Keep this file strictly about detecting signal.

Normalized payload shapes (adapters in Step 3 will produce these):

    users: list of dicts with keys
        id, email, is_admin (bool), has_mfa (bool),
        last_login (ISO-8601 string or None)

    shares: list of dicts with keys
        id, name, scope ("anonymous" | "public" | "organization" | "private")

    config: dict with keys
        audit_log_enabled (bool)
"""

from datetime import datetime, timezone
from typing import Any


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def check_admin_ratio(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not users:
        return []
    total = len(users)
    admins = [u for u in users if u.get("is_admin")]
    admin_count = len(admins)
    if admin_count == 0:
        return []
    ratio = admin_count / total
    if ratio <= 0.20:
        return []

    admin_emails = [u.get("email") or u.get("id") for u in admins if u.get("email") or u.get("id")]
    return [{
        "check_id": "admin_ratio",
        "severity": "high",
        "technical_detail": (
            f"{admin_count} of {total} users hold administrative privileges "
            f"({ratio * 100:.0f}%), above the 20% threshold. Admins: "
            f"{', '.join(str(e) for e in admin_emails[:10])}"
            f"{'…' if len(admin_emails) > 10 else ''}."
        ),
        "recommended_action": (
            "Reduce the number of accounts with admin access to 2-3 "
            "dedicated break-glass accounts and grant day-to-day users "
            "the least privilege needed to perform their role."
        ),
    }]


def check_mfa_coverage(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for u in users:
        if u.get("has_mfa"):
            continue
        identifier = u.get("email") or u.get("id") or "unknown user"
        findings.append({
            "check_id": "mfa_coverage",
            "severity": "critical" if u.get("is_admin") else "high",
            "technical_detail": (
                f"Account {identifier} "
                f"{'(admin)' if u.get('is_admin') else ''} "
                "does not have multi-factor authentication enrolled."
            ).strip(),
            "recommended_action": (
                f"Enforce MFA enrolment for {identifier} before next login, "
                "using an authenticator app or hardware key rather than SMS."
            ),
        })
    return findings


def check_dormant_users(users: list[dict[str, Any]], threshold_days: int = 90) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    findings: list[dict[str, Any]] = []
    for u in users:
        last_login = _parse_iso(u.get("last_login"))
        identifier = u.get("email") or u.get("id") or "unknown user"
        days_inactive: int | None = None
        never_logged_in = False
        if last_login is None:
            never_logged_in = True
        else:
            days_inactive = (now - last_login).days
            if days_inactive <= threshold_days:
                continue

        findings.append({
            "check_id": "dormant_users",
            "severity": "medium",
            "technical_detail": (
                f"Account {identifier} has not signed in for "
                f"{'never' if never_logged_in else f'{days_inactive} days'}, "
                f"exceeding the {threshold_days}-day dormancy threshold."
            ),
            "recommended_action": (
                f"Disable or remove {identifier} if no longer required, "
                "or document a business reason for retaining the account."
            ),
        })
    return findings


def check_public_sharing(shares: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for s in shares:
        scope = (s.get("scope") or "").lower()
        if scope not in ("anonymous", "public"):
            continue
        name = s.get("name") or s.get("id") or "unnamed resource"
        findings.append({
            "check_id": "public_sharing",
            "severity": "high",
            "technical_detail": (
                f"Resource '{name}' is shared publicly (scope='{scope}') "
                "and is accessible without authentication."
            ),
            "recommended_action": (
                f"Restrict '{name}' to specific users or groups, or revoke "
                "the public link if the resource is no longer intended to be public."
            ),
        })
    return findings


def check_audit_log_enabled(config: dict[str, Any]) -> list[dict[str, Any]]:
    if config.get("audit_log_enabled"):
        return []
    return [{
        "check_id": "audit_log_enabled",
        "severity": "high",
        "technical_detail": (
            "Audit logging is disabled on this SaaS tenant. Without audit logs "
            "there is no record of who performed security-relevant actions."
        ),
        "recommended_action": (
            "Enable audit logging (and forward logs to a retention store of "
            "at least 12 months) so security incidents can be investigated."
        ),
    }]


CHECK_REGISTRY = {
    "admin_ratio": check_admin_ratio,
    "mfa_coverage": check_mfa_coverage,
    "dormant_users": check_dormant_users,
    "public_sharing": check_public_sharing,
    "audit_log_enabled": check_audit_log_enabled,
}
