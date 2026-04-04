# backend/services/scheduler.py
# SecureIT360 — Automated scheduler
# Daily scans at 6am NZ time
# Weekly director email every Monday 8am NZ time
# Monthly report on 1st of every month 9am NZ time

import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone
import pytz

from services.email_service import (
    send_alert_email,
    send_weekly_director_email,
    send_monthly_report_email,
)

NZ_TIMEZONE = pytz.timezone("Pacific/Auckland")
scheduler = AsyncIOScheduler(timezone=NZ_TIMEZONE)


# ─── Daily Scan Job ───────────────────────────────────────────────────────────

async def run_daily_scans(supabase):
    """
    Runs every day at 6am NZ time.
    Loops all active tenants and triggers a full scan for each.
    Sends alert email if new critical findings are found.
    """
    print(f"[Scheduler] Daily scan started at {datetime.now(NZ_TIMEZONE)}")

    try:
        # Get all active tenants
        result = supabase.table("tenants").select("*").eq("status", "active").execute()
        tenants = result.data or []

        print(f"[Scheduler] Running scans for {len(tenants)} tenants")

        for tenant in tenants:
            try:
                await scan_tenant_and_alert(tenant, supabase)
            except Exception as e:
                print(f"[Scheduler] Error scanning tenant {tenant.get('id')}: {e}")

    except Exception as e:
        print(f"[Scheduler] Daily scan error: {e}")


async def scan_tenant_and_alert(tenant, supabase):
    """
    Scans a single tenant and sends alert if new critical findings found.
    """
    tenant_id = tenant.get("id")
    company_name = tenant.get("company_name", "Your company")

    # Get tenant owner email
    user_result = supabase.table("tenant_users")\
        .select("users(email)")\
        .eq("tenant_id", tenant_id)\
        .eq("role", "owner")\
        .execute()

    owner_email = None
    if user_result.data:
        owner_email = user_result.data[0].get("users", {}).get("email")

    if not owner_email:
        print(f"[Scheduler] No owner email for tenant {tenant_id}")
        return

    # Get previous scan findings
    prev_scan = supabase.table("scans")\
        .select("id")\
        .eq("tenant_id", tenant_id)\
        .eq("status", "complete")\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()

    prev_findings = set()
    if prev_scan.data:
        prev_scan_id = prev_scan.data[0]["id"]
        prev_result = supabase.table("findings")\
            .select("title")\
            .eq("scan_id", prev_scan_id)\
            .execute()
        prev_findings = {f["title"] for f in (prev_result.data or [])}

    # Trigger new scan via scan orchestrator
    from services.scan_orchestrator import run_full_scan
    domains_result = supabase.table("domains")\
        .select("domain")\
        .eq("tenant_id", tenant_id)\
        .execute()

    domains = [d["domain"] for d in (domains_result.data or [])]
    if not domains:
        return

    new_scan_id = await run_full_scan(tenant_id, domains[0], supabase)

    # Get new findings
    new_result = supabase.table("findings")\
        .select("*")\
        .eq("scan_id", new_scan_id)\
        .eq("severity", "critical")\
        .execute()

    new_findings = new_result.data or []

    # Find findings that weren't in previous scan
    truly_new = [f for f in new_findings if f.get("title") not in prev_findings]

    # Send alert if new critical findings found
    if truly_new:
        print(f"[Scheduler] Sending alert to {owner_email} — {len(truly_new)} new critical findings")
        send_alert_email(company_name, owner_email, truly_new)


# ─── Weekly Director Email Job ────────────────────────────────────────────────

async def run_weekly_director_emails(supabase):
    """
    Runs every Monday at 8am NZ time.
    Sends weekly summary to all active tenant owners.
    """
    print(f"[Scheduler] Weekly director emails started at {datetime.now(NZ_TIMEZONE)}")

    try:
        result = supabase.table("tenants").select("*").eq("status", "active").execute()
        tenants = result.data or []

        for tenant in tenants:
            try:
                await send_weekly_email_for_tenant(tenant, supabase)
            except Exception as e:
                print(f"[Scheduler] Error sending weekly email for tenant {tenant.get('id')}: {e}")

    except Exception as e:
        print(f"[Scheduler] Weekly email error: {e}")


async def send_weekly_email_for_tenant(tenant, supabase):
    """Sends weekly summary email for a single tenant."""
    tenant_id = tenant.get("id")
    company_name = tenant.get("company_name", "Your company")

    # Get owner email
    user_result = supabase.table("tenant_users")\
        .select("users(email)")\
        .eq("tenant_id", tenant_id)\
        .eq("role", "owner")\
        .execute()

    owner_email = None
    if user_result.data:
        owner_email = user_result.data[0].get("users", {}).get("email")

    if not owner_email:
        return

    # Get current score
    current_scan = supabase.table("scans")\
        .select("ransom_risk_score, governance_score")\
        .eq("tenant_id", tenant_id)\
        .eq("status", "complete")\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()

    current_score = 50
    if current_scan.data:
        current_score = current_scan.data[0].get("ransom_risk_score", 50)

    # Get previous week score
    prev_scan = supabase.table("scans")\
        .select("ransom_risk_score")\
        .eq("tenant_id", tenant_id)\
        .eq("status", "complete")\
        .order("created_at", desc=True)\
        .limit(2)\
        .execute()

    previous_score = current_score
    if prev_scan.data and len(prev_scan.data) > 1:
        previous_score = prev_scan.data[1].get("ransom_risk_score", current_score)

    # Get top 3 critical findings
    latest_scan = supabase.table("scans")\
        .select("id")\
        .eq("tenant_id", tenant_id)\
        .eq("status", "complete")\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()

    top_actions = []
    if latest_scan.data:
        scan_id = latest_scan.data[0]["id"]
        findings = supabase.table("findings")\
            .select("*")\
            .eq("scan_id", scan_id)\
            .order("severity", desc=True)\
            .limit(3)\
            .execute()
        top_actions = findings.data or []

    send_weekly_director_email(
        company_name=company_name,
        to_email=owner_email,
        current_score=current_score,
        previous_score=previous_score,
        top_actions=top_actions,
    )


# ─── Monthly Report Job ───────────────────────────────────────────────────────

async def run_monthly_reports(supabase):
    """
    Runs on the 1st of every month at 9am NZ time.
    Sends monthly report to all active tenant owners.
    """
    print(f"[Scheduler] Monthly reports started at {datetime.now(NZ_TIMEZONE)}")

    try:
        result = supabase.table("tenants").select("*").eq("status", "active").execute()
        tenants = result.data or []

        for tenant in tenants:
            try:
                await send_monthly_report_for_tenant(tenant, supabase)
            except Exception as e:
                print(f"[Scheduler] Error sending monthly report for tenant {tenant.get('id')}: {e}")

    except Exception as e:
        print(f"[Scheduler] Monthly report error: {e}")


async def send_monthly_report_for_tenant(tenant, supabase):
    """Sends monthly report email for a single tenant."""
    tenant_id = tenant.get("id")
    company_name = tenant.get("company_name", "Your company")

    # Get owner email
    user_result = supabase.table("tenant_users")\
        .select("users(email)")\
        .eq("tenant_id", tenant_id)\
        .eq("role", "owner")\
        .execute()

    owner_email = None
    if user_result.data:
        owner_email = user_result.data[0].get("users", {}).get("email")

    if not owner_email:
        return

    # Get current score
    current_scan = supabase.table("scans")\
        .select("ransom_risk_score")\
        .eq("tenant_id", tenant_id)\
        .eq("status", "complete")\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()

    current_score = 50
    if current_scan.data:
        current_score = current_scan.data[0].get("ransom_risk_score", 50)

    # Get total findings
    latest_scan = supabase.table("scans")\
        .select("id")\
        .eq("tenant_id", tenant_id)\
        .eq("status", "complete")\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()

    total_findings = 0
    fixed_this_month = 0

    if latest_scan.data:
        scan_id = latest_scan.data[0]["id"]
        findings = supabase.table("findings")\
            .select("id, status")\
            .eq("scan_id", scan_id)\
            .execute()

        all_findings = findings.data or []
        total_findings = len(all_findings)
        fixed_this_month = len([f for f in all_findings if f.get("status") == "fixed"])

    send_monthly_report_email(
        company_name=company_name,
        to_email=owner_email,
        current_score=current_score,
        total_findings=total_findings,
        fixed_this_month=fixed_this_month,
    )


# ─── Scheduler Setup ──────────────────────────────────────────────────────────

def start_scheduler(supabase):
    """
    Call this from main.py on startup.
    Registers all scheduled jobs.
    """

    # Daily scan — 6am NZ time every day
    scheduler.add_job(
        run_daily_scans,
        CronTrigger(hour=6, minute=0, timezone=NZ_TIMEZONE),
        args=[supabase],
        id="daily_scans",
        replace_existing=True,
    )

    # Weekly director email — Monday 8am NZ time
    scheduler.add_job(
        run_weekly_director_emails,
        CronTrigger(day_of_week="mon", hour=8, minute=0, timezone=NZ_TIMEZONE),
        args=[supabase],
        id="weekly_emails",
        replace_existing=True,
    )

    # Monthly report — 1st of every month 9am NZ time
    scheduler.add_job(
        run_monthly_reports,
        CronTrigger(day=1, hour=9, minute=0, timezone=NZ_TIMEZONE),
        args=[supabase],
        id="monthly_reports",
        replace_existing=True,
    )

    scheduler.start()
    print("[Scheduler] Started — daily scans 6am, weekly emails Monday 8am, monthly reports 1st of month 9am")