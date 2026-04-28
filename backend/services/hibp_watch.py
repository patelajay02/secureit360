"""Real-time HIBP breach watch.

Runs every 5 minutes via APScheduler (registered from backend/main.py).
For every (tenant, domain) row in hibp_breach_watch, asks HIBP whether
any new breaches have been published since we last looked. For each
genuinely new breach:

    * insert one row into findings (engine='darkweb_realtime')
    * insert one row into hibp_breach_alerts
    * fire send_critical_alert_email() for the tenant's director
    * advance last_checked_breach_name to the newest seen

First-run protection: if last_checked_breach_name is NULL on a watch row
we DO NOT fire alerts for the historical breach list — we just record
the current state. Otherwise day-1 of a new tenant would flood them with
every breach their domain has ever appeared in.

The sibling backend/services/darkweb_scan.py still runs the scheduled
deep darkweb scan against /breacheddomain/{domain}; this service is
purely about minutes-not-days detection of newly published breaches.
The two are intentionally independent.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Any

import httpx

from services.database import supabase_admin
from services.email_service import send_critical_alert_email


HIBP_BASE = "https://haveibeenpwned.com/api/v3"
USER_AGENT = "SecureIT360"

# Be polite between domains so we don't trip HIBP's rate limit even if a
# single tenant has many watched domains.
INTER_DOMAIN_DELAY_SECONDS = 1.5


def _hibp_headers() -> dict[str, str]:
    api_key = os.getenv("HIBP_API_KEY")
    if not api_key:
        raise RuntimeError("HIBP_API_KEY is not set")
    return {"hibp-api-key": api_key, "user-agent": USER_AGENT}


def _parse_added_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _sort_breaches_newest_first(breaches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    return sorted(
        breaches,
        key=lambda b: _parse_added_date(b.get("AddedDate")) or epoch,
        reverse=True,
    )


# ── HIBP REST calls ────────────────────────────────────────────────────────

async def _fetch_breaches_for_domain(
    client: httpx.AsyncClient,
    domain: str,
) -> list[dict[str, Any]]:
    resp = await client.get(
        f"{HIBP_BASE}/breaches",
        params={"Domain": domain},
        headers=_hibp_headers(),
        timeout=15,
    )
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    return resp.json() or []


async def _fetch_affected_emails(
    client: httpx.AsyncClient,
    domain: str,
) -> dict[str, list[str]]:
    """Returns {alias: [breach_names]} for the domain."""
    resp = await client.get(
        f"{HIBP_BASE}/breacheddomain/{domain}",
        headers=_hibp_headers(),
        timeout=20,
    )
    if resp.status_code == 404:
        return {}
    resp.raise_for_status()
    return resp.json() or {}


# ── Helpers ────────────────────────────────────────────────────────────────

def _count_affected_for_breach(
    affected_map: dict[str, list[str]],
    breach_name: str,
) -> int:
    return sum(
        1 for aliases in affected_map.values() if breach_name in (aliases or [])
    )


def _resolve_recipient_email(tenant_id: str) -> str | None:
    """Mirror the scheduler's "director_email -> owner" fallback so the
    real-time watch sends to the same person as the weekly summary."""
    try:
        t = (
            supabase_admin.table("tenants")
            .select("director_email")
            .eq("id", tenant_id)
            .single()
            .execute()
        )
        if t.data and t.data.get("director_email"):
            return t.data["director_email"]
    except Exception:
        pass

    try:
        tu = (
            supabase_admin.table("tenant_users")
            .select("user_id")
            .eq("tenant_id", tenant_id)
            .eq("role", "owner")
            .limit(1)
            .execute()
        )
        if tu.data:
            user = supabase_admin.auth.admin.get_user_by_id(tu.data[0]["user_id"])
            if user and user.user:
                return user.user.email
    except Exception as e:
        print(f"[HIBP watch] could not resolve recipient for tenant {tenant_id}: {e}")
    return None


def _alert_already_sent(tenant_id: str, breach_name: str) -> bool:
    """Idempotency guard. If the scheduler restarts mid-iteration we do
    not want to email the same tenant about the same breach twice."""
    try:
        r = (
            supabase_admin.table("hibp_breach_alerts")
            .select("id")
            .eq("tenant_id", tenant_id)
            .eq("breach_name", breach_name)
            .limit(1)
            .execute()
        )
        return bool(r.data)
    except Exception:
        return False


# ── Per-watch processing ───────────────────────────────────────────────────

async def _process_watch_row(
    client: httpx.AsyncClient,
    watch: dict[str, Any],
) -> None:
    tenant_id = watch["tenant_id"]
    domain = watch["domain"]
    last_seen = watch.get("last_checked_breach_name")

    breaches = await _fetch_breaches_for_domain(client, domain)
    if not breaches:
        supabase_admin.table("hibp_breach_watch").update({
            "last_checked_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", watch["id"]).execute()
        return

    sorted_breaches = _sort_breaches_newest_first(breaches)
    newest_name = sorted_breaches[0].get("Name")

    # First-run protection: don't replay history.
    if not last_seen:
        supabase_admin.table("hibp_breach_watch").update({
            "last_checked_breach_name": newest_name,
            "last_checked_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", watch["id"]).execute()
        return

    # Anything ABOVE the previously-seen entry in newest-first order is new.
    boundary_idx = next(
        (i for i, b in enumerate(sorted_breaches) if b.get("Name") == last_seen),
        len(sorted_breaches),
    )
    new_breaches = sorted_breaches[:boundary_idx]
    if not new_breaches:
        supabase_admin.table("hibp_breach_watch").update({
            "last_checked_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", watch["id"]).execute()
        return

    # One /breacheddomain call per scheduler tick per domain — reused for
    # every new breach in this tick.
    try:
        affected_map = await _fetch_affected_emails(client, domain)
    except Exception as e:
        print(f"[HIBP watch] /breacheddomain failed for {domain}: {e}")
        affected_map = {}

    recipient = _resolve_recipient_email(tenant_id)

    for breach in new_breaches:
        breach_name = breach.get("Name") or "unknown breach"

        if _alert_already_sent(tenant_id, breach_name):
            continue

        breach_date = breach.get("BreachDate")
        added_date = breach.get("AddedDate")
        try:
            pwn_count = int(breach.get("PwnCount") or 0)
        except (TypeError, ValueError):
            pwn_count = 0
        affected_count = _count_affected_for_breach(affected_map, breach_name)

        severity = "critical" if pwn_count > 100_000 else "moderate"
        title = f"New breach published: {breach_name} affecting {domain}"
        description = (
            f"{breach_name} was just published by Have I Been Pwned. "
            f"{affected_count} of your business email addresses appear in this breach. "
            f"Total accounts in this breach: {pwn_count:,}."
        )
        try:
            supabase_admin.table("findings").insert({
                "tenant_id": tenant_id,
                "engine": "darkweb_realtime",
                "severity": severity,
                "title": title,
                "description": description,
                "governance_gap": (
                    "No formal process exists to monitor employee credentials "
                    "against breach databases."
                ),
                "fix_type": "specialist",
                "score_impact": min(25, affected_count * 2 + 5),
                "status": "open",
                "auto_fixable": False,
            }).execute()
        except Exception as e:
            print(
                f"[HIBP watch] insert finding failed "
                f"(tenant={tenant_id}, breach={breach_name}): {e}"
            )

        try:
            supabase_admin.table("hibp_breach_alerts").insert({
                "tenant_id": tenant_id,
                "breach_name": breach_name,
                "breach_date": breach_date,
                "pwn_count": pwn_count,
                "affected_emails": affected_count,
                "email_recipient": recipient,
            }).execute()
        except Exception as e:
            print(
                f"[HIBP watch] insert alert failed "
                f"(tenant={tenant_id}, breach={breach_name}): {e}"
            )

        if recipient:
            try:
                send_critical_alert_email(
                    tenant_id=tenant_id,
                    breach_name=breach_name,
                    affected_count=affected_count,
                    domain=domain,
                    breach_date=breach_date,
                    pwn_count=pwn_count,
                    breach_added_date=added_date,
                    to_email=recipient,
                )
            except Exception as e:
                print(
                    f"[HIBP watch] email send failed "
                    f"(tenant={tenant_id}, breach={breach_name}): {e}"
                )

    supabase_admin.table("hibp_breach_watch").update({
        "last_checked_breach_name": newest_name,
        "last_checked_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", watch["id"]).execute()


# ── Entry point used by the scheduler ──────────────────────────────────────

async def check_for_new_breaches() -> None:
    """Scheduler entry point. Never raises — every error is logged and
    swallowed so a single bad domain or HIBP hiccup never crashes the
    APScheduler instance the rest of the platform depends on."""
    try:
        watches = supabase_admin.table("hibp_breach_watch").select("*").execute()
    except Exception as e:
        print(f"[HIBP watch] could not read hibp_breach_watch: {e}")
        return

    rows = watches.data or []
    if not rows:
        return

    try:
        async with httpx.AsyncClient() as client:
            for row in rows:
                try:
                    await _process_watch_row(client, row)
                except Exception as e:
                    print(
                        f"[HIBP watch] error processing "
                        f"{row.get('tenant_id')}/{row.get('domain')}: {e}"
                    )
                    continue
                await asyncio.sleep(INTER_DOMAIN_DELAY_SECONDS)
    except Exception as e:
        print(f"[HIBP watch] unrecoverable error in check_for_new_breaches: {e}")
