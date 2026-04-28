# backend/services/email_service.py
# SecureIT360 — Email service
# Sends alert emails and weekly director summary via SendGrid

import os
import hashlib
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = "governance@secureit360.co"
FROM_NAME = "Global Cyber Assurance"
SUPPORT_EMAIL = "support@secureit360.co"
GOVERNANCE_EMAIL = "governance@secureit360.co"
DASHBOARD_URL = "https://app.secureit360.co/dashboard"
BASE_URL = "https://app.secureit360.co"


def get_unsubscribe_link(email: str) -> str:
    token = hashlib.sha256(f"{email}{os.getenv('SENDGRID_API_KEY')}".encode()).hexdigest()
    return f"{BASE_URL}/unsubscribe?email={email}&token={token}"


def send_email(to_email: str, subject: str, html_body: str):
    try:
        message = Mail(
            from_email=(FROM_EMAIL, FROM_NAME),
            to_emails=to_email,
            subject=subject,
            html_content=html_body,
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        print(f"Email send error: {e}")
        return None


def footer_html(to_email: str) -> str:
    unsubscribe_url = get_unsubscribe_link(to_email)
    return f"""
    <div style="background:#f3f4f6; border-radius:0 0 12px 12px; padding:20px 32px;
                border:1px solid #e5e7eb; border-top:none;">
        <p style="color:#6b7280; font-size:13px; margin:0 0 8px 0;">
            Some findings require policy and governance work to resolve permanently.
            Contact us at <a href="mailto:{SUPPORT_EMAIL}" style="color:#dc2626;">{SUPPORT_EMAIL}</a> for guidance.
        </p>
        <p style="color:#9ca3af; font-size:12px; margin:0 0 8px 0;">
            Global Cyber Assurance — SecureIT360 — Complete cyber protection for businesses in Australia, the UAE, India and New Zealand.
        </p>
        <p style="color:#9ca3af; font-size:11px; margin:0;">
            You are receiving this email because you have an active SecureIT360 account.<br>
            <a href="{unsubscribe_url}" style="color:#9ca3af;">Unsubscribe from these emails</a>
        </p>
    </div>
    """


# ─── Critical Alert Email ─────────────────────────────────────────────────────

def send_alert_email(company_name: str, to_email: str, findings: list):
    if not findings:
        return

    findings_html = ""
    for f in findings:
        findings_html += f"""
        <tr>
            <td style="padding:12px 16px; border-bottom:1px solid #fee2e2;">
                <strong style="color:#dc2626;">{f.get('title', 'Security issue found')}</strong><br>
                <span style="color:#374151; font-size:14px;">{f.get('description', '')}</span>
            </td>
        </tr>
        """

    subject = f"⚠️ New security risk found — {company_name}"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f9fafb; font-family: Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:32px 16px;">

            <div style="background:#111827; border-radius:12px 12px 0 0; padding:24px 32px;">
                <h1 style="color:#fff; margin:0; font-size:22px;">
                    SecureIT<span style="color:#dc2626;">360</span>
                    <span style="color:#9ca3af; font-weight:400;"> Security Alert</span>
                </h1>
                <p style="color:#6b7280; margin:4px 0 0 0; font-size:13px;">by Global Cyber Assurance</p>
            </div>

            <div style="background:#ffffff; padding:32px; border-left:1px solid #e5e7eb; border-right:1px solid #e5e7eb;">
                <p style="color:#111827; font-size:16px; margin-top:0;">Hi {company_name} team,</p>
                <p style="color:#374151; font-size:15px;">
                    Our daily scan found <strong>{len(findings)} new security risk{"s" if len(findings) > 1 else ""}</strong> that need your attention:
                </p>

                <table style="width:100%; border-collapse:collapse; margin:16px 0; background:#fef2f2;
                              border-radius:8px; border:1px solid #fee2e2;">
                    {findings_html}
                </table>

                <div style="text-align:center; margin:24px 0;">
                    <a href="{DASHBOARD_URL}"
                       style="background:#dc2626; color:#fff; padding:14px 32px; border-radius:8px;
                              text-decoration:none; font-weight:bold; font-size:15px;">
                        View my dashboard
                    </a>
                </div>

                <p style="color:#6b7280; font-size:13px;">
                    Our platform automatically fixes simple issues overnight.
                    Moderate issues include a step-by-step fix guide.
                    Critical issues are flagged for specialist review.
                </p>
            </div>

            {footer_html(to_email)}
        </div>
    </body>
    </html>
    """

    return send_email(to_email, subject, html_body)


# ─── Real-time HIBP Critical Breach Alert ───────────────────────────────────
# Fired by backend/services/hibp_watch.py within minutes of a new HIBP
# breach being published that affects a verified tenant domain. Distinct
# from send_alert_email above, which is the daily-scan-results format.

def _human_relative(dt_str: str | None) -> str:
    if not dt_str:
        return "recently"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return "recently"
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    delta = now - dt
    secs = max(0, int(delta.total_seconds()))
    if secs < 3600:
        m = max(1, secs // 60)
        return f"{m} minute{'s' if m != 1 else ''} ago"
    if secs < 86_400:
        h = secs // 3600
        return f"{h} hour{'s' if h != 1 else ''} ago"
    d = secs // 86_400
    return f"{d} day{'s' if d != 1 else ''} ago"


def send_critical_alert_email(
    tenant_id: str,
    breach_name: str,
    affected_count: int,
    *,
    domain: str,
    breach_date: str | None = None,
    pwn_count: int | None = None,
    breach_added_date: str | None = None,
    to_email: str | None = None,
) -> int | None:
    # Resolve company_name and recipient if the caller didn't pre-fetch them.
    company_name = "Your company"
    try:
        from services.database import supabase_admin  # local import: avoid circular at module load
        t = (
            supabase_admin.table("tenants")
            .select("name, director_email")
            .eq("id", tenant_id)
            .single()
            .execute()
        )
        if t.data:
            company_name = t.data.get("name") or company_name
            if not to_email:
                to_email = t.data.get("director_email")
    except Exception as e:
        print(f"[critical alert] tenant lookup failed for {tenant_id}: {e}")

    if not to_email:
        print(f"[critical alert] no recipient email for tenant {tenant_id} — skipping")
        return None

    when_phrase = _human_relative(breach_added_date)
    pwn_count_pretty = f"{pwn_count:,}" if isinstance(pwn_count, int) else "an unknown number of"
    breach_date_pretty = breach_date or "Unknown"

    subject = f"Critical: New data breach affecting {domain}"

    governance_gap = (
        "No formal process exists to monitor employee credentials against "
        "breach databases."
    )

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f9fafb; font-family: Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:32px 16px;">

            <div style="background:#111827; border-radius:12px 12px 0 0; padding:24px 32px;">
                <h1 style="color:#fff; margin:0; font-size:22px;">
                    SecureIT<span style="color:#dc2626;">360</span>
                    <span style="color:#9ca3af; font-weight:400;"> Real-time Breach Alert</span>
                </h1>
                <p style="color:#6b7280; margin:4px 0 0 0; font-size:13px;">by Global Cyber Assurance</p>
            </div>

            <div style="background:#ffffff; padding:32px; border-left:1px solid #e5e7eb; border-right:1px solid #e5e7eb;">
                <p style="color:#111827; font-size:16px; margin-top:0;">Hi {company_name} team,</p>

                <p style="color:#374151; font-size:15px; line-height:1.6;">
                    A new breach was published <strong>{when_phrase}</strong> affecting your verified domain
                    <strong>{domain}</strong>.
                    <strong>{affected_count}</strong> of your business email addresses appear in this breach.
                </p>

                <table style="width:100%; border-collapse:collapse; margin:16px 0; background:#fef2f2;
                              border-radius:8px; border:1px solid #fee2e2;">
                    <tr>
                        <td style="padding:12px 16px; border-bottom:1px solid #fee2e2; color:#6b7280; font-size:13px; width:42%;">Breach name</td>
                        <td style="padding:12px 16px; border-bottom:1px solid #fee2e2; color:#111827; font-size:14px; font-weight:600;">{breach_name}</td>
                    </tr>
                    <tr>
                        <td style="padding:12px 16px; border-bottom:1px solid #fee2e2; color:#6b7280; font-size:13px;">Breach date</td>
                        <td style="padding:12px 16px; border-bottom:1px solid #fee2e2; color:#111827; font-size:14px;">{breach_date_pretty}</td>
                    </tr>
                    <tr>
                        <td style="padding:12px 16px; color:#6b7280; font-size:13px;">Total accounts in breach</td>
                        <td style="padding:12px 16px; color:#111827; font-size:14px;">{pwn_count_pretty}</td>
                    </tr>
                </table>

                <p style="color:#9ca3af; font-style:italic; font-size:13px; margin:18px 0 0 0;">
                    {governance_gap}
                </p>

                <p style="color:#6b7280; font-size:13px; margin:18px 0 0 0;">
                    For incident response support contact
                    <a href="mailto:governance@globalcyberassurance.com" style="color:#6b7280;">governance@globalcyberassurance.com</a>
                </p>
            </div>

            {footer_html(to_email)}
        </div>
    </body>
    </html>
    """

    return send_email(to_email, subject, html_body)


# ─── Score Improvement Email ──────────────────────────────────────────────────

def send_score_improvement_email(company_name: str, to_email: str, old_score: int, new_score: int):
    improvement = old_score - new_score
    subject = f"Great news — your cyber risk score improved!"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f9fafb; font-family: Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:32px 16px;">

            <div style="background:#111827; border-radius:12px 12px 0 0; padding:24px 32px;">
                <h1 style="color:#fff; margin:0; font-size:22px;">
                    SecureIT<span style="color:#dc2626;">360</span>
                    <span style="color:#9ca3af; font-weight:400;"> Good News</span>
                </h1>
                <p style="color:#6b7280; margin:4px 0 0 0; font-size:13px;">by Global Cyber Assurance</p>
            </div>

            <div style="background:#ffffff; padding:32px; border-left:1px solid #e5e7eb; border-right:1px solid #e5e7eb;">
                <p style="color:#111827; font-size:16px; margin-top:0;">Hi {company_name} team,</p>
                <p style="color:#374151; font-size:15px;">Great news — your cyber risk score has improved this week.</p>

                <div style="text-align:center; background:#f0fdf4; border-radius:12px; padding:32px; margin:24px 0;">
                    <table style="width:100%; border-collapse:collapse;">
                        <tr>
                            <td style="text-align:center; width:40%;">
                                <div style="font-size:56px; font-weight:900; color:#dc2626;">{old_score}</div>
                                <div style="color:#6b7280; font-size:14px;">Last week</div>
                            </td>
                            <td style="text-align:center; width:20%; font-size:28px; color:#16a34a;">→</td>
                            <td style="text-align:center; width:40%;">
                                <div style="font-size:56px; font-weight:900; color:#16a34a;">{new_score}</div>
                                <div style="color:#6b7280; font-size:14px;">This week</div>
                            </td>
                        </tr>
                    </table>
                    <div style="margin-top:16px; color:#16a34a; font-weight:600; font-size:16px;">
                        ▼ Down {improvement} points — well done!
                    </div>
                </div>

                <div style="text-align:center; margin:24px 0;">
                    <a href="{DASHBOARD_URL}"
                       style="background:#16a34a; color:#fff; padding:14px 32px; border-radius:8px;
                              text-decoration:none; font-weight:bold; font-size:15px;">
                        View my dashboard
                    </a>
                </div>
            </div>

            {footer_html(to_email)}
        </div>
    </body>
    </html>
    """

    return send_email(to_email, subject, html_body)


# ─── Weekly Director Summary Email ───────────────────────────────────────────

def send_weekly_director_email(
    company_name: str,
    to_email: str,
    current_score: int,
    previous_score: int,
    top_actions: list,
    governance_score: int = None,
    director_liability_score: int = None,
    unresolved_findings: list = None,
):
    if unresolved_findings is None:
        unresolved_findings = []

    score_change = current_score - previous_score

    if score_change <= -10:
        send_score_improvement_email(company_name, to_email, previous_score, current_score)

    if score_change > 0:
        change_html = f'<span style="color:#dc2626;">▲ Up {score_change} points from last week</span>'
        change_note = "Your risk has increased this week. Please review the actions below."
    elif score_change < 0:
        change_html = f'<span style="color:#16a34a;">▼ Down {abs(score_change)} points from last week</span>'
        change_note = "Good progress — your risk score has improved this week."
    else:
        change_html = '<span style="color:#6b7280;">— No change from last week</span>'
        change_note = "Your risk level is unchanged this week."

    if current_score >= 60:
        score_color = "#dc2626"
        score_label = "High Risk"
    elif current_score >= 30:
        score_color = "#d97706"
        score_label = "Medium Risk"
    else:
        score_color = "#16a34a"
        score_label = "Low Risk"

    # Governance + Director Liability block
    if governance_score is not None:
        if governance_score >= 70:
            gov_color = "#16a34a"
            gov_label = "Strong"
        elif governance_score >= 40:
            gov_color = "#d97706"
            gov_label = "Moderate"
        else:
            gov_color = "#dc2626"
            gov_label = "Weak"

        liab_score = director_liability_score
        liab_color = "#dc2626" if (liab_score or 0) >= 60 else "#d97706" if (liab_score or 0) >= 30 else "#16a34a"
        liab_display = str(liab_score) if liab_score is not None else "—"

        governance_html = f"""
        <table style="width:100%; border-collapse:collapse; margin:24px 0;">
            <tr>
                <td style="width:50%; padding-right:8px;">
                    <div style="background:#f9fafb; border:1px solid #e5e7eb; border-radius:10px;
                                padding:20px; text-align:center;">
                        <div style="color:#6b7280; font-size:13px; margin-bottom:6px;">Governance Score</div>
                        <div style="font-size:42px; font-weight:900; color:{gov_color};">{governance_score}</div>
                        <div style="color:{gov_color}; font-size:13px; font-weight:600;">{gov_label}</div>
                    </div>
                </td>
                <td style="width:50%; padding-left:8px;">
                    <div style="background:#f9fafb; border:1px solid #e5e7eb; border-radius:10px;
                                padding:20px; text-align:center;">
                        <div style="color:#6b7280; font-size:13px; margin-bottom:6px;">Director Liability Score</div>
                        <div style="font-size:42px; font-weight:900; color:{liab_color};">{liab_display}</div>
                        <div style="color:#6b7280; font-size:12px; margin-top:4px;">Personal exposure risk</div>
                    </div>
                </td>
            </tr>
        </table>
        """
    else:
        governance_html = ""

    # Top 3 actions
    actions_html = ""
    for i, action in enumerate(top_actions[:3], 1):
        severity = action.get("severity", "medium")
        if severity == "critical":
            sev_color = "#dc2626"
            sev_bg = "#fef2f2"
        elif severity == "high":
            sev_color = "#d97706"
            sev_bg = "#fffbeb"
        else:
            sev_color = "#6b7280"
            sev_bg = "#f9fafb"

        actions_html += f"""
        <tr>
            <td style="padding:14px 16px; border-bottom:1px solid #f0f0f0; background:{sev_bg};">
                <table style="width:100%; border-collapse:collapse;">
                    <tr>
                        <td>
                            <strong style="color:#111827; font-size:15px;">{i}. {action.get('title', '')}</strong><br>
                            <span style="color:#374151; font-size:13px;">{action.get('description', '')}</span>
                        </td>
                        <td style="text-align:right; vertical-align:top; padding-left:12px;">
                            <span style="background:{sev_color}; color:#fff; font-size:11px; font-weight:600;
                                         padding:2px 8px; border-radius:12px; white-space:nowrap;">
                                {severity.upper()}
                            </span>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        """

    # Unresolved findings
    if unresolved_findings:
        unresolved_rows = ""
        for f in unresolved_findings[:10]:
            severity = f.get("severity", "medium")
            dot_color = "#dc2626" if severity == "critical" else "#d97706" if severity == "high" else "#6b7280"
            unresolved_rows += f"""
            <tr>
                <td style="padding:10px 16px; border-bottom:1px solid #f3f4f6;">
                    <span style="display:inline-block; width:8px; height:8px; border-radius:50%;
                                 background:{dot_color}; margin-right:8px; vertical-align:middle;"></span>
                    <span style="color:#111827; font-size:14px;">{f.get('title', '')}</span>
                </td>
            </tr>
            """
        extra = f"<p style='color:#6b7280; font-size:12px; margin-top:8px;'>Showing top 10 — view full list in your dashboard.</p>" if len(unresolved_findings) > 10 else ""
        unresolved_html = f"""
        <h2 style="color:#111827; font-size:16px; margin:28px 0 12px 0;">
            Unresolved findings ({len(unresolved_findings)})
        </h2>
        <table style="width:100%; border-collapse:collapse; border:1px solid #e5e7eb; border-radius:8px; overflow:hidden;">
            {unresolved_rows}
        </table>
        {extra}
        """
    else:
        unresolved_html = """
        <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; padding:16px;
                    margin:24px 0; text-align:center;">
            <span style="color:#16a34a; font-weight:600;">✓ No unresolved findings this week. Excellent work!</span>
        </div>
        """

    subject = f"{company_name} — weekly cyber security summary"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f9fafb; font-family: Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:32px 16px;">

            <div style="background:#111827; border-radius:12px 12px 0 0; padding:24px 32px;">
                <h1 style="color:#fff; margin:0; font-size:22px;">
                    SecureIT<span style="color:#dc2626;">360</span>
                    <span style="color:#9ca3af; font-weight:400; font-size:18px;"> Weekly Summary</span>
                </h1>
                <p style="color:#6b7280; margin:4px 0 0 0; font-size:13px;">
                    Global Cyber Assurance — {datetime.now().strftime("%A %d %B %Y")}
                </p>
            </div>

            <div style="background:#ffffff; padding:32px; border-left:1px solid #e5e7eb; border-right:1px solid #e5e7eb;">

                <p style="color:#111827; font-size:16px; margin-top:0;">Hi {company_name},</p>
                <p style="color:#374151; font-size:14px; margin-bottom:24px;">
                    Here is your weekly cyber security summary from Global Cyber Assurance.
                </p>

                <!-- Ransom Risk Score -->
                <div style="text-align:center; background:#f9fafb; border:1px solid #e5e7eb;
                            border-radius:12px; padding:28px; margin-bottom:8px;">
                    <p style="color:#6b7280; font-size:13px; margin:0 0 8px 0; text-transform:uppercase;
                              letter-spacing:0.05em;">Ransom Risk Score</p>
                    <div style="font-size:72px; font-weight:900; color:{score_color}; line-height:1;">
                        {current_score}
                    </div>
                    <div style="font-size:15px; color:{score_color}; font-weight:600; margin:4px 0;">
                        {score_label}
                    </div>
                    <div style="font-size:14px; margin-top:10px;">{change_html}</div>
                    <p style="color:#6b7280; font-size:13px; margin:6px 0 0 0;">{change_note}</p>
                </div>

                <!-- Governance + Director Liability -->
                {governance_html}

                <!-- Top 3 Actions -->
                <h2 style="color:#111827; font-size:16px; margin:28px 0 12px 0;">
                    Top 3 recommended actions
                </h2>
                <table style="width:100%; border-collapse:collapse; border:1px solid #e5e7eb;
                              border-radius:8px; overflow:hidden;">
                    {actions_html if actions_html else
                     '<tr><td style="padding:16px; color:#16a34a; font-weight:600;">✓ No critical actions this week. Great work!</td></tr>'}
                </table>

                <!-- Unresolved Findings -->
                {unresolved_html}

                <!-- CTA -->
                <div style="text-align:center; margin:32px 0 8px 0;">
                    <a href="{DASHBOARD_URL}"
                       style="background:#dc2626; color:#fff; padding:14px 36px; border-radius:8px;
                              text-decoration:none; font-weight:bold; font-size:15px;">
                        View full dashboard
                    </a>
                </div>

            </div>

            {footer_html(to_email)}
        </div>
    </body>
    </html>
    """

    return send_email(to_email, subject, html_body)


# ─── Monthly Report Email ─────────────────────────────────────────────────────

def send_monthly_report_email(
    company_name: str,
    to_email: str,
    current_score: int,
    total_findings: int,
    fixed_this_month: int,
):
    subject = f"{company_name} — monthly cyber security report"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f9fafb; font-family: Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:32px 16px;">

            <div style="background:#111827; border-radius:12px 12px 0 0; padding:24px 32px;">
                <h1 style="color:#fff; margin:0; font-size:22px;">
                    SecureIT<span style="color:#dc2626;">360</span>
                    <span style="color:#9ca3af; font-weight:400;"> Monthly Report</span>
                </h1>
                <p style="color:#6b7280; margin:4px 0 0 0; font-size:13px;">
                    Global Cyber Assurance — {datetime.now().strftime("%B %Y")}
                </p>
            </div>

            <div style="background:#ffffff; padding:32px; border-left:1px solid #e5e7eb; border-right:1px solid #e5e7eb;">
                <p style="color:#111827; font-size:16px; margin-top:0;">Hi {company_name},</p>
                <p style="color:#374151; font-size:15px;">
                    Here is your monthly cyber security report for {datetime.now().strftime("%B %Y")}.
                </p>

                <table style="width:100%; border-collapse:collapse; margin:24px 0;">
                    <tr>
                        <td style="width:33%; padding-right:8px;">
                            <div style="background:#f0fdf4; border-radius:8px; padding:20px; text-align:center;">
                                <div style="font-size:36px; font-weight:900; color:#16a34a;">{fixed_this_month}</div>
                                <div style="color:#374151; font-size:13px; margin-top:4px;">Issues fixed</div>
                            </div>
                        </td>
                        <td style="width:33%; padding:0 4px;">
                            <div style="background:#fef2f2; border-radius:8px; padding:20px; text-align:center;">
                                <div style="font-size:36px; font-weight:900; color:#dc2626;">{total_findings}</div>
                                <div style="color:#374151; font-size:13px; margin-top:4px;">Total findings</div>
                            </div>
                        </td>
                        <td style="width:33%; padding-left:8px;">
                            <div style="background:#f0f9ff; border-radius:8px; padding:20px; text-align:center;">
                                <div style="font-size:36px; font-weight:900; color:#0284c7;">{current_score}</div>
                                <div style="color:#374151; font-size:13px; margin-top:4px;">Risk score</div>
                            </div>
                        </td>
                    </tr>
                </table>

                <div style="text-align:center; margin:32px 0 16px 0;">
                    <a href="{DASHBOARD_URL}"
                       style="background:#dc2626; color:#fff; padding:14px 32px; border-radius:8px;
                              text-decoration:none; font-weight:bold; font-size:15px;">
                        View full report
                    </a>
                </div>
            </div>

            {footer_html(to_email)}
        </div>
    </body>
    </html>
    """

    return send_email(to_email, subject, html_body)