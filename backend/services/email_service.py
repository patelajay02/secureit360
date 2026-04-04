# backend/services/email_service.py
# SecureIT360 — Email service
# Sends alert emails and weekly director summary via SendGrid

import os
import hashlib
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = "hello@secureit360.co"
FROM_NAME = "SecureIT360 by Global Cyber Assurance"
SUPPORT_EMAIL = "support@secureit360.co"
GOVERNANCE_EMAIL = "governance@secureit360.co"
DASHBOARD_URL = "https://secureit360.co/dashboard"
BASE_URL = "https://secureit360.co"


def get_unsubscribe_link(email: str) -> str:
    """Generates a unique unsubscribe link for each email address."""
    token = hashlib.sha256(f"{email}{os.getenv('SENDGRID_API_KEY')}".encode()).hexdigest()
    return f"{BASE_URL}/unsubscribe?email={email}&token={token}"


def send_email(to_email: str, subject: str, html_body: str):
    """Core send function — all emails go through here."""
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
    """Standard footer with unsubscribe link — used in all emails."""
    unsubscribe_url = get_unsubscribe_link(to_email)
    return f"""
    <div style="background:#f3f4f6; border-radius:0 0 12px 12px; padding:20px 32px;
                border:1px solid #e5e7eb; border-top:none;">
        <p style="color:#6b7280; font-size:13px; margin:0 0 8px 0;">
            Some findings require policy and governance work to resolve permanently.
            Contact us at <a href="mailto:{GOVERNANCE_EMAIL}" style="color:#4f46e5;">{GOVERNANCE_EMAIL}</a> for guidance.
        </p>
        <p style="color:#9ca3af; font-size:12px; margin:0 0 8px 0;">
            SecureIT360 by Global Cyber Assurance — Complete cyber protection. Monitored daily. Fixed automatically.
        </p>
        <p style="color:#9ca3af; font-size:11px; margin:0;">
            You are receiving this email because you have an active SecureIT360 account.<br>
            <a href="{unsubscribe_url}" style="color:#9ca3af;">Unsubscribe from these emails</a>
        </p>
    </div>
    """


# ─── Critical Alert Email ─────────────────────────────────────────────────────

def send_alert_email(company_name: str, to_email: str, findings: list):
    """Sent immediately when a new critical finding is detected."""
    if not findings:
        return

    findings_html = ""
    for f in findings:
        findings_html += f"""
        <tr>
            <td style="padding: 12px 16px; border-bottom: 1px solid #f0f0f0;">
                <strong style="color: #dc2626;">{f.get('title', 'Security issue found')}</strong><br>
                <span style="color: #374151; font-size: 14px;">{f.get('plain_english', '')}</span>
            </td>
        </tr>
        """

    subject = f"New security risk found — {company_name}"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f9fafb; font-family: Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:32px 16px;">

            <div style="background:#1e1b4b; border-radius:12px 12px 0 0; padding:24px 32px;">
                <h1 style="color:#fff; margin:0; font-size:22px;">
                    SecureIT360 <span style="color:#818cf8;">Security Alert</span>
                </h1>
                <p style="color:#a5b4fc; margin:4px 0 0 0; font-size:14px;">
                    by Global Cyber Assurance
                </p>
            </div>

            <div style="background:#ffffff; padding:32px; border-left:1px solid #e5e7eb; border-right:1px solid #e5e7eb;">
                <p style="color:#111827; font-size:16px; margin-top:0;">
                    Hi {company_name} team,
                </p>
                <p style="color:#374151; font-size:15px;">
                    Our daily scan found <strong>{len(findings)} new security risk{"s" if len(findings) > 1 else ""}</strong>
                    that need your attention:
                </p>

                <table style="width:100%; border-collapse:collapse; margin:16px 0; background:#fef2f2; border-radius:8px;">
                    {findings_html}
                </table>

                <div style="text-align:center; margin:24px 0;">
                    <a href="{DASHBOARD_URL}"
                       style="background:#4f46e5; color:#fff; padding:14px 32px; border-radius:8px;
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


# ─── Score Improvement Email ──────────────────────────────────────────────────

def send_score_improvement_email(company_name: str, to_email: str, old_score: int, new_score: int):
    """Sent when score drops by 10 or more points — positive reinforcement."""
    improvement = old_score - new_score
    subject = f"Great news — your cyber security risk score improved!"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f9fafb; font-family: Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:32px 16px;">

            <div style="background:#1e1b4b; border-radius:12px 12px 0 0; padding:24px 32px;">
                <h1 style="color:#fff; margin:0; font-size:22px;">
                    SecureIT360 <span style="color:#818cf8;">Good News</span>
                </h1>
                <p style="color:#a5b4fc; margin:4px 0 0 0; font-size:14px;">
                    by Global Cyber Assurance
                </p>
            </div>

            <div style="background:#ffffff; padding:32px; border-left:1px solid #e5e7eb; border-right:1px solid #e5e7eb;">
                <p style="color:#111827; font-size:16px; margin-top:0;">
                    Hi {company_name} team,
                </p>
                <p style="color:#374151; font-size:15px;">
                    Great news — your cyber security risk score has improved!
                </p>

                <div style="text-align:center; background:#f0fdf4; border-radius:12px; padding:32px; margin:24px 0;">
                    <div style="display:flex; justify-content:center; align-items:center; gap:24px;">
                        <div>
                            <div style="font-size:48px; font-weight:900; color:#dc2626;">{old_score}</div>
                            <div style="color:#6b7280; font-size:14px;">Last week</div>
                        </div>
                        <div style="font-size:32px; color:#16a34a;">→</div>
                        <div>
                            <div style="font-size:48px; font-weight:900; color:#16a34a;">{new_score}</div>
                            <div style="color:#6b7280; font-size:14px;">This week</div>
                        </div>
                    </div>
                    <div style="margin-top:16px; color:#16a34a; font-weight:600; font-size:16px;">
                        ▼ Down {improvement} points — well done!
                    </div>
                </div>

                <p style="color:#374151; font-size:15px;">
                    Your team is making real progress in reducing your cyber security risk.
                    Keep going — log in to see what else you can improve.
                </p>

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
):
    """Sent every Monday at 8am NZ time."""

    score_change = current_score - previous_score

    # Check if score improved significantly — send improvement email too
    if score_change <= -10:
        send_score_improvement_email(company_name, to_email, previous_score, current_score)

    if score_change > 0:
        change_html = f'<span style="color:#dc2626;">▲ Up {score_change} points from last week</span>'
        change_note = "Your risk has increased. Please review the actions below."
    elif score_change < 0:
        change_html = f'<span style="color:#16a34a;">▼ Down {abs(score_change)} points from last week</span>'
        change_note = "Good progress — your risk score has improved."
    else:
        change_html = '<span style="color:#6b7280;">No change from last week</span>'
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

    actions_html = ""
    for i, action in enumerate(top_actions[:3], 1):
        actions_html += f"""
        <tr>
            <td style="padding:12px 16px; border-bottom:1px solid #f0f0f0;">
                <strong style="color:#111827;">{i}. {action.get('title', '')}</strong><br>
                <span style="color:#374151; font-size:14px;">{action.get('plain_english', '')}</span>
            </td>
        </tr>
        """

    subject = f"{company_name} — weekly cyber security summary"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f9fafb; font-family: Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:32px 16px;">

            <div style="background:#1e1b4b; border-radius:12px 12px 0 0; padding:24px 32px;">
                <h1 style="color:#fff; margin:0; font-size:22px;">
                    SecureIT360 <span style="color:#818cf8;">Weekly Summary</span>
                </h1>
                <p style="color:#a5b4fc; margin:4px 0 0 0; font-size:14px;">
                    by Global Cyber Assurance — {datetime.now().strftime("%A %d %B %Y")}
                </p>
            </div>

            <div style="background:#ffffff; padding:32px; border-left:1px solid #e5e7eb; border-right:1px solid #e5e7eb;">
                <p style="color:#111827; font-size:16px; margin-top:0;">
                    Hi {company_name} team,
                </p>
                <p style="color:#374151; font-size:15px;">
                    Here is your weekly cyber security summary.
                </p>

                <div style="text-align:center; background:#f9fafb; border-radius:12px; padding:32px; margin:24px 0;">
                    <p style="color:#6b7280; font-size:14px; margin:0 0 8px 0;">Your Ransom Risk Score</p>
                    <div style="font-size:72px; font-weight:900; color:{score_color}; line-height:1;">
                        {current_score}
                    </div>
                    <div style="font-size:16px; color:{score_color}; font-weight:600; margin:4px 0;">
                        {score_label}
                    </div>
                    <div style="font-size:14px; margin-top:8px;">
                        {change_html}
                    </div>
                    <p style="color:#6b7280; font-size:13px; margin:8px 0 0 0;">
                        {change_note}
                    </p>
                </div>

                <h2 style="color:#111827; font-size:17px; margin:24px 0 12px 0;">
                    Your top 3 actions this week
                </h2>
                <table style="width:100%; border-collapse:collapse; border-radius:8px; overflow:hidden; border:1px solid #e5e7eb;">
                    {actions_html if actions_html else '<tr><td style="padding:16px; color:#6b7280;">No critical actions this week. Great work!</td></tr>'}
                </table>

                <div style="text-align:center; margin:32px 0 16px 0;">
                    <a href="{DASHBOARD_URL}"
                       style="background:#4f46e5; color:#fff; padding:14px 32px; border-radius:8px;
                              text-decoration:none; font-weight:bold; font-size:15px;">
                        View my full dashboard
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
    """Sent on the 1st of every month."""

    subject = f"{company_name} — monthly cyber security report"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f9fafb; font-family: Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:32px 16px;">

            <div style="background:#1e1b4b; border-radius:12px 12px 0 0; padding:24px 32px;">
                <h1 style="color:#fff; margin:0; font-size:22px;">
                    SecureIT360 <span style="color:#818cf8;">Monthly Report</span>
                </h1>
                <p style="color:#a5b4fc; margin:4px 0 0 0; font-size:14px;">
                    by Global Cyber Assurance — {datetime.now().strftime("%B %Y")}
                </p>
            </div>

            <div style="background:#ffffff; padding:32px; border-left:1px solid #e5e7eb; border-right:1px solid #e5e7eb;">
                <p style="color:#111827; font-size:16px; margin-top:0;">
                    Hi {company_name} team,
                </p>
                <p style="color:#374151; font-size:15px;">
                    Here is your monthly cyber security report for {datetime.now().strftime("%B %Y")}.
                </p>

                <div style="display:flex; gap:16px; margin:24px 0;">
                    <div style="flex:1; background:#f0fdf4; border-radius:8px; padding:20px; text-align:center;">
                        <div style="font-size:36px; font-weight:900; color:#16a34a;">{fixed_this_month}</div>
                        <div style="color:#374151; font-size:14px; margin-top:4px;">Issues fixed this month</div>
                    </div>
                    <div style="flex:1; background:#fef2f2; border-radius:8px; padding:20px; text-align:center;">
                        <div style="font-size:36px; font-weight:900; color:#dc2626;">{total_findings}</div>
                        <div style="color:#374151; font-size:14px; margin-top:4px;">Total findings</div>
                    </div>
                    <div style="flex:1; background:#f0f9ff; border-radius:8px; padding:20px; text-align:center;">
                        <div style="font-size:36px; font-weight:900; color:#0284c7;">{current_score}</div>
                        <div style="color:#374151; font-size:14px; margin-top:4px;">Current risk score</div>
                    </div>
                </div>

                <div style="text-align:center; margin:32px 0 16px 0;">
                    <a href="{DASHBOARD_URL}"
                       style="background:#4f46e5; color:#fff; padding:14px 32px; border-radius:8px;
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