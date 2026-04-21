# SecureIT360 - Ransom Risk Score Calculator
# This is the hero feature. Calculates a score out of 100.
# Higher score = higher risk of ransomware attack.
# Red above 60. Amber 30-60. Green below 30.
# The score is calculated entirely from scan findings - no questionnaire needed.

from services.database import supabase_admin


# Calculate the Ransom Risk Score for a tenant
def calculate_ransom_score(tenant_id: str, scan_id: str) -> dict:
    try:
        # Get all open findings for this scan
        findings = supabase_admin.table("findings")\
            .select("*")\
            .eq("tenant_id", tenant_id)\
            .eq("scan_id", scan_id)\
            .eq("status", "open")\
            .execute()

        # Start with a perfect score and deduct points for each finding
        base_score = 100
        total_deduction = 0
        critical_count = 0
        moderate_count = 0
        low_count = 0

        for finding in findings.data:
            score_impact = finding.get("score_impact", 0)
            severity = finding.get("severity", "low")

            # Only deduct points for actual risk findings
            if score_impact > 0:
                total_deduction += score_impact

            if severity == "critical":
                critical_count += 1
            elif severity == "moderate":
                moderate_count += 1
            else:
                low_count += 1

        # Calculate final score (minimum 0, maximum 100)
        ransom_score = max(0, min(100, total_deduction))

        # Determine risk label
        if ransom_score >= 60:
            risk_label = "High Risk"
        elif ransom_score >= 30:
            risk_label = "Medium Risk"
        else:
            risk_label = "Low Risk"

        # Calculate financial impact estimates based on score
        if ransom_score >= 60:
            ransom_demand_min = 85000
            ransom_demand_max = 220000
            downtime_days_min = 14
            downtime_days_max = 28
            director_liability = "High"
        elif ransom_score >= 30:
            ransom_demand_min = 25000
            ransom_demand_max = 85000
            downtime_days_min = 7
            downtime_days_max = 14
            director_liability = "Medium"
        else:
            ransom_demand_min = 5000
            ransom_demand_max = 25000
            downtime_days_min = 1
            downtime_days_max = 7
            director_liability = "Low"

        # Update the scan record with the score
        supabase_admin.table("scans")\
            .update({
                "ransom_score": ransom_score,
                "risk_label": risk_label,
                "status": "complete"
            })\
            .eq("id", scan_id)\
            .eq("tenant_id", tenant_id)\
            .execute()

        return {
            "ransom_score": ransom_score,
            "risk_label": risk_label,
            "critical_findings": critical_count,
            "moderate_findings": moderate_count,
            "low_findings": low_count,
            "total_findings": len(findings.data),
            "if_attacked_today": {
                "ransom_demand_min_nzd": ransom_demand_min,
                "ransom_demand_max_nzd": ransom_demand_max,
                "downtime_days_min": downtime_days_min,
                "downtime_days_max": downtime_days_max,
                "director_liability": director_liability,
                "regulatory_fine_nz": "Up to NZD $10,000",
                "regulatory_fine_au": "Up to AUD $50,000,000"
            }
        }

    except Exception as e:
        return {"error": str(e)}


# Calculate Governance Score from the same findings
def calculate_governance_score(tenant_id: str, scan_id: str) -> dict:
    try:
        # Get all findings for this scan
        findings = supabase_admin.table("findings")\
            .select("governance_gap, engine")\
            .eq("tenant_id", tenant_id)\
            .eq("scan_id", scan_id)\
            .execute()

        # Count unique governance domains affected
        governance_domains = {
            "Access control governance": False,
            "Staff training and awareness": False,
            "Network security governance": False,
            "Asset management": False,
            "Email security governance": False,
            "Data governance": False,
            "Patch governance": False,
            "Business continuity": False
        }

        for finding in findings.data:
            gap = finding.get("governance_gap", "").lower()
            engine = finding.get("engine", "")

            if "access control" in gap or "mfa" in gap:
                governance_domains["Access control governance"] = True
            if "training" in gap or "awareness" in gap:
                governance_domains["Staff training and awareness"] = True
            if "network" in gap or "firewall" in gap:
                governance_domains["Network security governance"] = True
            if "asset" in gap or "lifecycle" in gap or "ssl" in gap:
                governance_domains["Asset management"] = True
            if "email" in gap:
                governance_domains["Email security governance"] = True
            if "data" in gap or "classification" in gap or "cloud" in gap:
                governance_domains["Data governance"] = True
            if "patch" in gap or "update" in gap:
                governance_domains["Patch governance"] = True
            if "continuity" in gap or "backup" in gap or "recovery" in gap:
                governance_domains["Business continuity"] = True

        # Count how many domains have gaps
        domains_with_gaps = sum(1 for v in governance_domains.values() if v)
        total_domains = len(governance_domains)

        # Governance score - lower is better here
        # 0 gaps = 100 score, all gaps = 0 score
        governance_score = int(
            ((total_domains - domains_with_gaps) / total_domains) * 100
        )

        # Update scan with governance score
        supabase_admin.table("scans")\
            .update({"governance_score": governance_score})\
            .eq("id", scan_id)\
            .eq("tenant_id", tenant_id)\
            .execute()

        return {
            "governance_score": governance_score,
            "domains_affected": domains_with_gaps,
            "total_domains": total_domains,
            "governance_gaps": {
                domain: "Gap identified" if has_gap else "No gap found"
                for domain, has_gap in governance_domains.items()
            }
        }

    except Exception as e:
        return {"error": str(e)}


def calculate_director_liability_score(tenant_id: str, scan_id: str) -> dict:
    """
    Compute director personal liability score from MS365, Google Workspace,
    and threat intel findings across ALL open tenant findings.
    Stored against the triggering scan for record-keeping.
    """
    try:
        findings = supabase_admin.table("findings")\
            .select("engine, title")\
            .eq("tenant_id", tenant_id)\
            .eq("status", "open")\
            .execute()

        score = 0
        for f in findings.data:
            engine = f.get("engine", "")
            title = (f.get("title") or "").lower()

            if engine in ("microsoft365", "google_workspace"):
                if "inactive" in title and "account" in title:
                    score += 10
                elif "mfa" in title or "2-step" in title or "2sv" in title:
                    score += 5
                elif "admin" in title and "privilege" in title:
                    score += 15

            elif engine == "threat_intel":
                if "data breach" in title or ("email account" in title and "exposed" in title):
                    score += 20
                elif "typosquat" in title or "impersonat" in title:
                    score += 25
                elif "flagged" in title and ("ip address" in title or "blacklist" in title or "abuse" in title):
                    score += 10

        director_liability_score = min(100, score)

        supabase_admin.table("scans")\
            .update({"director_liability_score": director_liability_score})\
            .eq("id", scan_id)\
            .eq("tenant_id", tenant_id)\
            .execute()

        return {"director_liability_score": director_liability_score}

    except Exception as e:
        return {"error": str(e)}