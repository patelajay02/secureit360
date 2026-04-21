import os
import json
import httpx
from datetime import datetime, timezone, timedelta
from services.database import supabase_admin

ADMIN_BASE = "https://admin.googleapis.com/admin/directory/v1"
DRIVE_BASE = "https://www.googleapis.com/drive/v3"
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _sanitize_metadata(obj: dict) -> dict:
    return json.loads(json.dumps(obj, default=str))


def _get_frameworks(country: str, extra: list) -> list:
    c = (country or "NZ").upper()
    if c in ("UAE", "AE"):
        base = ["UAE PDPL 2021", "DIFC Data Protection Law", "ADGM", "ISO 27001"]
    elif c == "AU":
        base = ["Australian Privacy Act 1988", "ISO 27001", "ASD Essential Eight"]
    elif c == "IN":
        base = ["DPDP Act 2023", "RBI Guidelines", "CERT-In", "ISO 27001"]
    else:
        base = ["NZ Privacy Act 2020", "ISO 27001", "ASD Essential Eight"]
    return list(dict.fromkeys(base + (extra or [])))


async def _refresh_token(integration: dict) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "refresh_token",
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "refresh_token": integration["refresh_token"],
            },
            timeout=20,
        )
        resp.raise_for_status()
        td = resp.json()

    new_token = td["access_token"]
    new_refresh = td.get("refresh_token", integration["refresh_token"])
    expires_in = td.get("expires_in", 3600)
    new_expiry = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

    supabase_admin.table("integrations").update({
        "access_token": new_token,
        "refresh_token": new_refresh,
        "token_expires_at": new_expiry,
    }).eq("id", integration["id"]).execute()

    return new_token


async def _get_token(integration: dict) -> str:
    expires_at = integration.get("token_expires_at")
    if expires_at:
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) < expiry - timedelta(minutes=5):
            return integration["access_token"]
    return await _refresh_token(integration)


async def _api_get(token: str, base: str, path: str, params: dict = None) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{base}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=30,
        )
        if resp.status_code in (403, 429):
            return {}
        resp.raise_for_status()
        return resp.json()


def _parse_last_login(value: str | None) -> datetime | None:
    """Return None if the timestamp is missing or is the Google epoch placeholder."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt <= _EPOCH + timedelta(days=1):
            return None
        return dt
    except Exception:
        return None


async def run_google_workspace_scan(tenant_id: str, scan_id: str) -> dict:
    result = supabase_admin.table("integrations")\
        .select("*")\
        .eq("tenant_id", tenant_id)\
        .eq("platform", "google_workspace")\
        .eq("status", "connected")\
        .single()\
        .execute()

    if not result.data:
        return {"findings_count": 0, "skipped": True}

    integration = result.data

    tenant_r = supabase_admin.table("tenants")\
        .select("country, compliance_frameworks")\
        .eq("id", tenant_id)\
        .single()\
        .execute()

    country = "NZ"
    extra_frameworks: list = []
    if tenant_r.data:
        country = tenant_r.data.get("country") or "NZ"
        extra_frameworks = tenant_r.data.get("compliance_frameworks") or []

    frameworks = _get_frameworks(country, extra_frameworks)

    try:
        token = await _get_token(integration)
    except Exception as e:
        return {"findings_count": 0, "error": str(e)}

    # Fetch all users once — reused by checks 1, 2, and 3
    all_users = []
    try:
        data = await _api_get(token, ADMIN_BASE, "/users", params={
            "customer": "my_customer",
            "maxResults": "200",
            "projection": "full",
            "orderBy": "email",
        })
        all_users = data.get("users", [])
    except Exception as e:
        print(f"[GWS] Failed to fetch users: {e}")

    findings = []

    # 1 — MFA / 2SV STATUS
    try:
        no_2sv = [u for u in all_users if not u.get("isEnrolledIn2Sv", False)]
        if no_2sv:
            n = len(no_2sv)
            findings.append({
                "tenant_id": tenant_id,
                "scan_id": scan_id,
                "engine": "google_workspace",
                "severity": "critical",
                "title": f"Google MFA not enabled for {n} Workspace user{'s' if n > 1 else ''}",
                "description": (
                    f"{n} account{'s' if n > 1 else ''} in your Google Workspace domain "
                    "do not have 2-Step Verification enrolled. "
                    "These accounts can be compromised through password spray or phishing alone."
                ),
                "governance_gap": True,
                "regulations": frameworks,
                "fix_type": "voice",
                "score_impact": min(25, n * 3),
                "status": "open",
                "metadata": _sanitize_metadata({
                    "affected_users": [
                        {
                            "name": u.get("name", {}).get("fullName", "Unknown"),
                            "email": u.get("primaryEmail", ""),
                            "google_user_id": u.get("id"),
                            "last_login": u.get("lastLoginTime"),
                            "recommended_action": "Enable 2-Step Verification immediately",
                        }
                        for u in no_2sv
                    ]
                }),
            })
    except Exception as e:
        print(f"[GWS] MFA check failed: {e}")

    # 2 — INACTIVE USERS (90+ days)
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        inactive = []
        for u in all_users:
            last_login = _parse_last_login(u.get("lastLoginTime"))
            if last_login is None or last_login < cutoff:
                inactive.append(u)

        if inactive:
            n = len(inactive)
            findings.append({
                "tenant_id": tenant_id,
                "scan_id": scan_id,
                "engine": "google_workspace",
                "severity": "moderate",
                "title": f"{n} inactive Google Workspace account{'s' if n > 1 else ''} (90+ days)",
                "description": (
                    f"{n} user account{'s' if n > 1 else ''} have not signed in to Google Workspace for over 90 days. "
                    "Stale accounts expand your attack surface and should be suspended or removed."
                ),
                "governance_gap": True,
                "regulations": frameworks,
                "fix_type": "voice",
                "score_impact": min(15, n * 2),
                "status": "open",
                "metadata": _sanitize_metadata({
                    "affected_users": [
                        {
                            "name": u.get("name", {}).get("fullName", "Unknown"),
                            "email": u.get("primaryEmail", ""),
                            "google_user_id": u.get("id"),
                            "last_login": u.get("lastLoginTime") or "Never",
                            "recommended_action": "Suspend or remove account",
                        }
                        for u in inactive
                    ]
                }),
            })
    except Exception as e:
        print(f"[GWS] Inactive users check failed: {e}")

    # 3 — ADMIN PRIVILEGE SPRAWL
    try:
        admins = [
            u for u in all_users
            if u.get("isAdmin", False) or u.get("isDelegatedAdmin", False)
        ]
        if len(admins) > 3:
            n = len(admins)
            findings.append({
                "tenant_id": tenant_id,
                "scan_id": scan_id,
                "engine": "google_workspace",
                "severity": "moderate",
                "title": f"{n} accounts with Google admin privilege{'s' if n > 1 else ''} in Google Workspace",
                "description": (
                    f"{n} accounts have admin roles in your Google Workspace domain. "
                    "Excessive admin accounts amplify the blast radius of any account compromise. "
                    "Best practice is to limit admin access to 2–3 dedicated accounts."
                ),
                "governance_gap": True,
                "regulations": frameworks,
                "fix_type": "voice",
                "score_impact": min(15, n * 2),
                "status": "open",
                "metadata": _sanitize_metadata({
                    "affected_users": [
                        {
                            "name": u.get("name", {}).get("fullName", "Unknown"),
                            "email": u.get("primaryEmail", ""),
                            "google_user_id": u.get("id"),
                            "roles": "Super Admin" if u.get("isAdmin") else "Delegated Admin",
                            "last_login": u.get("lastLoginTime"),
                            "recommended_action": "Review and remove unnecessary admin access",
                        }
                        for u in admins
                    ]
                }),
            })
    except Exception as e:
        print(f"[GWS] Admin check failed: {e}")

    # 4 — EXTERNAL FILE SHARING (Google Drive)
    try:
        drive_data = await _api_get(token, DRIVE_BASE, "/files", params={
            "q": "visibility='anyoneWithLink' or visibility='anyoneCanFind'",
            "fields": "files(id,name,visibility)",
            "pageSize": "50",
            "corpora": "domain",
            "includeItemsFromAllDrives": "true",
            "supportsAllDrives": "true",
        })
        external_files = drive_data.get("files", [])
        if external_files:
            external_count = len(external_files)
            findings.append({
                "tenant_id": tenant_id,
                "scan_id": scan_id,
                "engine": "google_workspace",
                "severity": "critical" if external_count > 10 else "moderate",
                "title": f"{external_count} file{'s' if external_count > 1 else ''} shared externally in Google Workspace",
                "description": (
                    f"{external_count} file{'s' if external_count > 1 else ''} in your Google Drive "
                    "are shared externally or via public link. "
                    "Uncontrolled external sharing can expose sensitive business data to unauthorised parties."
                ),
                "governance_gap": True,
                "regulations": frameworks,
                "fix_type": "voice",
                "score_impact": min(20, external_count * 2),
                "status": "open",
                "metadata": _sanitize_metadata({"external_share_count": external_count}),
            })
    except Exception as e:
        print(f"[GWS] External sharing check failed: {e}")

    inserted = 0
    for finding in findings:
        try:
            supabase_admin.table("findings").insert(finding).execute()
            inserted += 1
        except Exception as e:
            print(f"[GWS] Failed to insert finding '{finding.get('title', '?')}': {e}")

    supabase_admin.table("integrations")\
        .update({"last_synced_at": datetime.now(timezone.utc).isoformat()})\
        .eq("id", integration["id"])\
        .execute()

    return {"findings_count": inserted}
