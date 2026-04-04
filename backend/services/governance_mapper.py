# SecureIT360 - Governance Mapper
# This file maps each finding type to its governance gap text.
# Every technical problem reveals a governance failure automatically.
# These lines appear as plain grey text below each finding - never as a sales pitch.

GOVERNANCE_GAPS = {
    "darkweb": (
        "No staff security awareness training program exists. "
        "Staff are not aware of the risks of reusing passwords."
    ),
    "email_dmarc": (
        "No email security policy exists. "
        "Your business has no protection against email impersonation attacks."
    ),
    "email_spf": (
        "No email security policy exists."
    ),
    "network_rdp": (
        "No network security policy or firewall management process exists. "
        "Nobody is responsible for monitoring open network access points."
    ),
    "network_open_port": (
        "No network security policy exists. "
        "There is no process for reviewing and closing unnecessary network access."
    ),
    "ssl_expired": (
        "No asset lifecycle management process exists. "
        "SSL certificates are not being tracked or renewed before expiry."
    ),
    "ssl_missing_headers": (
        "No web security policy exists. "
        "Website security configuration is not being managed or reviewed."
    ),
    "devices_unpatched": (
        "No patch management process exists. "
        "Devices are not being updated on a regular schedule."
    ),
    "cloud_public_storage": (
        "No data classification policy exists. "
        "Staff are not aware of how to store sensitive business data securely."
    ),
    "no_backups": (
        "No business continuity plan exists. "
        "The business has no documented plan for recovering from a ransomware attack."
    ),
    "no_mfa": (
        "No access control policy exists. "
        "There is no requirement for staff to use strong authentication."
    ),
    "no_incident_plan": (
        "No incident response plan exists. "
        "The business does not know what to do if a cyber attack occurs."
    )
}

def get_governance_gap(finding_type: str) -> str:
    return GOVERNANCE_GAPS.get(
        finding_type,
        "This finding indicates a governance gap — technical fixes alone will not prevent this recurring."
    )