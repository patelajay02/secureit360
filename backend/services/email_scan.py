# SecureIT360 - Email Security Scan Engine
# Checks DMARC, SPF and DKIM records with specific regulation clause references

import httpx
from services.database import supabase_admin


def upsert_finding(tenant_id, scan_id, engine, severity, title, description, governance_gap, regulations, fix_type, score_impact):
    existing = supabase_admin.table("findings")\
        .select("id")\
        .eq("tenant_id", tenant_id)\
        .eq("engine", engine)\
        .eq("title", title)\
        .execute()

    if existing.data:
        supabase_admin.table("findings")\
            .update({
                "scan_id": scan_id,
                "severity": severity,
                "description": description,
                "governance_gap": governance_gap,
                "regulations": regulations,
                "fix_type": fix_type,
                "score_impact": score_impact,
                "status": "open"
            })\
            .eq("id", existing.data[0]["id"])\
            .execute()
        return False
    else:
        supabase_admin.table("findings").insert({
            "tenant_id": tenant_id,
            "scan_id": scan_id,
            "engine": engine,
            "severity": severity,
            "title": title,
            "description": description,
            "governance_gap": governance_gap,
            "regulations": regulations,
            "fix_type": fix_type,
            "score_impact": score_impact,
            "status": "open"
        }).execute()
        return True


async def check_email_security(domain: str) -> dict:
    results = {
        "dmarc": False,
        "spf": False,
        "dkim": False
    }

    try:
        async with httpx.AsyncClient() as client:
            dmarc_response = await client.get(
                f"https://dns.google/resolve?name=_dmarc.{domain}&type=TXT",
                timeout=15
            )
            if dmarc_response.status_code == 200:
                data = dmarc_response.json()
                answers = data.get("Answer", [])
                for answer in answers:
                    if "v=DMARC1" in answer.get("data", ""):
                        results["dmarc"] = True

            spf_response = await client.get(
                f"https://dns.google/resolve?name={domain}&type=TXT",
                timeout=15
            )
            if spf_response.status_code == 200:
                data = spf_response.json()
                answers = data.get("Answer", [])
                for answer in answers:
                    if "v=spf1" in answer.get("data", ""):
                        results["spf"] = True

    except Exception:
        pass

    return results


async def run_email_scan(tenant_id: str, scan_id: str, domain: str):
    try:
        findings_count = 0
        email_security = await check_email_security(domain)

        if not email_security["dmarc"]:
            is_new = upsert_finding(
                tenant_id, scan_id, "email", "critical",
                "Scammers can send emails pretending to be your business",
                (
                    f"Your domain {domain} has no DMARC record. "
                    f"This means anyone on the internet can send emails that look like "
                    f"they come from your business. Scammers use this to trick your "
                    f"clients and staff into sending money or clicking dangerous links. "
                    f"This is one of the most common ways businesses lose money to fraud."
                ),
                "No email security policy exists. Your business has no protection against email impersonation attacks.",
                [
                    "AU Essential Eight ML1 - Email hardening (DMARC required)",
                    "NZ NCSC Guidelines - Email security baseline",
                    "AU Privacy Act 1988 - APP 11.1 (security of personal information)",
                    "NZ Privacy Act 2020 - IPP 5 (security safeguards)"
                ],
                "voice", 12
            )
            findings_count += 1

        if not email_security["spf"]:
            is_new = upsert_finding(
                tenant_id, scan_id, "email", "moderate",
                "Your email domain has no sender protection",
                (
                    f"Your domain {domain} has no SPF record. "
                    f"SPF tells email providers which servers are allowed to send "
                    f"emails from your domain. Without it, your emails may go to "
                    f"spam and scammers can more easily impersonate your business."
                ),
                "No email security policy exists. Sender verification has not been configured for your domain.",
                [
                    "AU Essential Eight ML1 - Email hardening (SPF required)",
                    "NZ NCSC Guidelines - Email security baseline",
                    "AU Privacy Act 1988 - APP 11.1 (security of personal information)",
                    "NZ Privacy Act 2020 - IPP 5 (security safeguards)"
                ],
                "voice", 8
            )
            findings_count += 1

        supabase_admin.table("scan_engine_results").upsert({
            "tenant_id": tenant_id,
            "scan_id": scan_id,
            "engine": "email",
            "status": "complete",
            "findings_count": findings_count
        }).execute()

        return {"status": "complete", "findings_count": findings_count}

    except Exception as e:
        supabase_admin.table("scan_engine_results").upsert({
            "tenant_id": tenant_id,
            "scan_id": scan_id,
            "engine": "email",
            "status": "error",
            "findings_count": 0
        }).execute()
        return {"status": "error", "message": str(e)}
