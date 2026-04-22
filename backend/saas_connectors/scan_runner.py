"""Scan runner for the Universal SaaS Connector.

run_scan(connection_id) orchestrates a single scan:

    1. Load the connection record and decrypt its credentials.
    2. Look up the app's generic_check_capabilities in saas_app_registry.
    3. Call the adapter for the app_slug (Step 3 will wire real adapters)
       to return normalized payloads keyed by check_id.
    4. Run each applicable generic check.
    5. Map every raw finding through governance_mapper for the user's
       country, then persist to saas_findings.
    6. Update saas_connections.last_scan_at and return a summary.
"""

from datetime import datetime, timezone
from typing import Any

from services.database import supabase_admin

from .credential_vault import load_credentials
from .generic_checks import CHECK_REGISTRY
from .governance_mapper import map_to_governance


# ── Adapter placeholder ─────────────────────────────────────────────────────
# Real per-SaaS adapters land in Step 3. Each adapter accepts the
# decrypted credentials dict and a list of capability keys, and returns
# a payload dict keyed by the capability it satisfies, e.g.:
#     {"admin_ratio": <users list>, "mfa_coverage": <users list>,
#      "public_sharing": <shares list>, "audit_log_enabled": <config dict>}

def _placeholder_adapter(
    app_slug: str,  # noqa: ARG001 — used by real adapters
    credentials: dict[str, Any],  # noqa: ARG001
    capabilities: list[str],  # noqa: ARG001
) -> dict[str, Any]:
    """Stub adapter. Real implementations land in Step 3."""
    return {}


ADAPTERS: dict[str, Any] = {}


def _get_adapter(app_slug: str):
    return ADAPTERS.get(app_slug, _placeholder_adapter)


# ── User country lookup ─────────────────────────────────────────────────────

def _user_country(user_id: str) -> str:
    try:
        tu = (
            supabase_admin.table("tenant_users")
            .select("tenant_id")
            .eq("user_id", user_id)
            .eq("status", "active")
            .limit(1)
            .execute()
        )
        if not tu.data:
            return "NZ"
        tenant_id = tu.data[0]["tenant_id"]
        t = (
            supabase_admin.table("tenants")
            .select("country")
            .eq("id", tenant_id)
            .single()
            .execute()
        )
        return (t.data or {}).get("country") or "NZ"
    except Exception:
        return "NZ"


# ── Main entry point ────────────────────────────────────────────────────────

def run_scan(connection_id: str) -> dict[str, Any]:
    conn_r = (
        supabase_admin.table("saas_connections")
        .select("id, user_id, app_slug, app_name, connection_type")
        .eq("id", connection_id)
        .single()
        .execute()
    )
    if not conn_r.data:
        raise ValueError("Connection not found")

    connection = conn_r.data
    user_id = connection["user_id"]
    app_slug = connection["app_slug"]

    credentials = load_credentials(connection_id, user_id)

    registry_r = (
        supabase_admin.table("saas_app_registry")
        .select("generic_check_capabilities")
        .eq("slug", app_slug)
        .single()
        .execute()
    )
    capabilities: list[str] = []
    if registry_r.data:
        caps = registry_r.data.get("generic_check_capabilities") or []
        if isinstance(caps, list):
            capabilities = [str(c) for c in caps]

    adapter = _get_adapter(app_slug)
    payloads = adapter(app_slug, credentials, capabilities) or {}

    country = _user_country(user_id)

    raw_findings: list[dict[str, Any]] = []
    for cap in capabilities:
        check_fn = CHECK_REGISTRY.get(cap)
        if not check_fn:
            continue
        payload = payloads.get(cap)
        if payload is None:
            continue
        try:
            raw_findings.extend(check_fn(payload))
        except Exception as e:
            print(f"[SaaS scan] check {cap} failed for {app_slug}: {e}")

    severity_breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    inserted = 0
    for raw in raw_findings:
        mapped = map_to_governance(raw, country)
        severity = mapped.get("severity") or "info"
        severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1
        try:
            supabase_admin.table("saas_findings").insert({
                "connection_id": connection_id,
                "check_id": mapped["check_id"],
                "severity": severity,
                "governance_statement": mapped["governance_statement"],
                "technical_detail": mapped.get("technical_detail"),
                "recommended_action": mapped["recommended_action"],
                "regulation_refs": mapped["regulation_refs"],
            }).execute()
            inserted += 1
        except Exception as e:
            print(f"[SaaS scan] failed to insert finding '{mapped.get('check_id')}': {e}")

    supabase_admin.table("saas_connections").update({
        "last_scan_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", connection_id).execute()

    return {
        "connection_id": connection_id,
        "findings_count": inserted,
        "severity_breakdown": severity_breakdown,
    }
