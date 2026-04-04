# SecureIT360 - Regulatory Mapping Engine
# Maps every finding to every regulation it breaches.
# The client never needs to know which law applies.
# The platform handles it invisibly.

REGULATORY_MAPPINGS = {
    "darkweb": {
        "regulations": [
            "NZ Privacy Act 2020 — Principle 5: Must protect personal information",
            "NZ Privacy Act 2020 — Section 113: Breach notification within 72 hours",
            "AU Privacy Act 1988 — APP 11: Security of personal information",
            "AU Privacy Act 1988 — Notifiable Data Breach Scheme"
        ],
        "plain_english": "A data breach involving staff emails may trigger mandatory reporting obligations under both NZ and AU privacy law."
    },
    "email": {
        "regulations": [
            "AU Essential Eight — ML1: Configure Microsoft Office macro settings",
            "AU Essential Eight — ML2: User application hardening",
            "NZ NCSC Guidelines — Email security baseline controls"
        ],
        "plain_english": "Missing email security records means your business cannot prove it took reasonable steps to prevent email fraud."
    },
    "network": {
        "regulations": [
            "AU Essential Eight — Restrict administrative privileges",
            "AU Essential Eight — Patch operating systems",
            "NZ NCSC Guidelines — Network security baseline",
            "NZ Companies Act 1993 — Director duty of care"
        ],
        "plain_english": "Open network ports that allow unauthorised access represent a failure of director duty of care under both NZ and AU law."
    },
    "website": {
        "regulations": [
            "NZ Privacy Act 2020 — Principle 5: Security safeguards",
            "AU Privacy Act 1988 — APP 11: Technical security measures",
            "AU Essential Eight — Patch applications"
        ],
        "plain_english": "An expired or invalid SSL certificate means customer data submitted on your website may not be properly protected."
    },
    "devices": {
        "regulations": [
            "AU Essential Eight — Patch applications: Within 48 hours for critical",
            "AU Essential Eight — Patch operating systems",
            "NZ NCSC Guidelines — Patch management",
            "ISO 27001 — A.12.6: Technical vulnerability management"
        ],
        "plain_english": "Unpatched devices are the leading cause of ransomware infections and represent a clear failure of reasonable security measures."
    },
    "cloud": {
        "regulations": [
            "NZ Privacy Act 2020 — Principle 5: Must protect personal information",
            "NZ Privacy Act 2020 — Section 113: Notifiable privacy breach",
            "AU Privacy Act 1988 — APP 11: Security of personal information",
            "AU Privacy Act 1988 — Notifiable Data Breach Scheme",
            "AU Corporations Act 2001 — Section 180: Director duty of care"
        ],
        "plain_english": "Publicly accessible cloud storage containing personal information is a notifiable privacy breach under both NZ and AU law. Directors may face personal liability."
    }
}

# Severity to regulation urgency mapping
SEVERITY_URGENCY = {
    "critical": "Immediate action required — regulatory breach confirmed",
    "moderate": "Action required within 30 days — regulatory risk identified",
    "low": "Action recommended — potential regulatory exposure"
}

def get_regulatory_mapping(engine: str) -> dict:
    return REGULATORY_MAPPINGS.get(engine, {
        "regulations": [],
        "plain_english": "This finding may have regulatory implications. Please review with your compliance advisor."
    })

def get_urgency(severity: str) -> str:
    return SEVERITY_URGENCY.get(severity, "Review recommended")


# Generate a full compliance gap report for a scan
def generate_compliance_report(tenant_id: str, scan_id: str, findings: list) -> dict:
    breached_regulations = set()
    compliance_gaps = []

    for finding in findings:
        engine = finding.get("engine", "")
        severity = finding.get("severity", "low")
        mapping = get_regulatory_mapping(engine)

        if mapping["regulations"] and finding.get("score_impact", 0) > 0:
            for reg in mapping["regulations"]:
                breached_regulations.add(reg)

            compliance_gaps.append({
                "finding": finding.get("title"),
                "severity": severity,
                "urgency": get_urgency(severity),
                "regulations_breached": mapping["regulations"],
                "plain_english": mapping["plain_english"]
            })

    return {
        "total_regulations_breached": len(breached_regulations),
        "regulations_breached": list(breached_regulations),
        "compliance_gaps": compliance_gaps,
        "frameworks_affected": get_frameworks_affected(breached_regulations)
    }


def get_frameworks_affected(regulations: set) -> list:
    frameworks = []
    reg_text = " ".join(regulations)

    if "NZ Privacy Act" in reg_text:
        frameworks.append("NZ Privacy Act 2020")
    if "AU Privacy Act" in reg_text:
        frameworks.append("AU Privacy Act 1988")
    if "Essential Eight" in reg_text:
        frameworks.append("AU Essential Eight (ACSC)")
    if "NCSC" in reg_text:
        frameworks.append("NZ NCSC Guidelines")
    if "Companies Act" in reg_text:
        frameworks.append("NZ Companies Act 1993")
    if "Corporations Act" in reg_text:
        frameworks.append("AU Corporations Act 2001")
    if "ISO 27001" in reg_text:
        frameworks.append("ISO 27001")

    return frameworks