# backend/routes/email_preview.py
# SecureIT360 — Email preview endpoint
# Visit /email/preview/alert or /email/preview/weekly to see exactly what clients receive

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from services.email_service import (
    send_alert_email,
    send_weekly_director_email,
    send_monthly_report_email,
    send_score_improvement_email,
)

router = APIRouter()

SAMPLE_COMPANY = "Acme Plumbing Ltd"
SAMPLE_EMAIL = "preview@secureit360.co"

SAMPLE_FINDINGS = [
    {
        "title": "Passwords found on the dark web",
        "plain_english": "2 staff email addresses and passwords have been found in a hacker database. Anyone with this information could access your systems right now.",
        "severity": "critical",
    },
    {
        "title": "No multi-factor authentication",
        "plain_english": "Your accounts have no second layer of protection. If a password is stolen, hackers can log straight in with no barrier.",
        "severity": "critical",
    },
]

SAMPLE_ACTIONS = [
    {
        "title": "Enable multi-factor authentication",
        "plain_english": "Turn on two-step login for all staff accounts. This one step stops 99% of account takeover attacks.",
    },
    {
        "title": "Reset compromised passwords",
        "plain_english": "Change the passwords for 2 staff accounts found in hacker databases immediately.",
    },
    {
        "title": "Set up email protection",
        "plain_english": "Your domain has no DMARC record. Scammers can send emails pretending to be you to your clients and suppliers.",
    },
]


@router.get("/preview/alert", response_class=HTMLResponse)
def preview_alert_email():
    """Preview the critical alert email."""
    from services.email_service import footer_html
    from services.email_service import DASHBOARD_URL

    findings_html = ""
    for f in SAMPLE_FINDINGS:
        findings_html += f"""
        <tr>
            <td style="padding: 12px 16px; border-bottom: 1px solid #f0f0f0;">
                <strong style="color: #dc2626;">{f.get('title')}</strong><br>
                <span style="color: #374151; font-size: 14px;">{f.get('plain_english')}</span>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f9fafb; font-family: Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:32px 16px;">

            <!-- Preview banner -->
            <div style="background:#fef3c7; border:1px solid #f59e0b; border-radius:8px; 
                        padding:12px 16px; margin-bottom:16px; text-align:center;">
                <strong style="color:#92400e;">📧 EMAIL PREVIEW MODE — This is exactly what your clients will receive</strong>
            </div>

            <div style="background:#1e1b4b; border-radius:12px 12px 0 0; padding:24px 32px;">
                <h1 style="color:#fff; margin:0; font-size:22px;">
                    SecureIT360 <span style="color:#818cf8;">Security Alert</span>
                </h1>
                <p style="color:#a5b4fc; margin:4px 0 0 0; font-size:14px;">by Global Cyber Assurance</p>
            </div>

            <div style="background:#ffffff; padding:32px; border-left:1px solid #e5e7eb; border-right:1px solid #e5e7eb;">
                <p style="color:#111827; font-size:16px; margin-top:0;">Hi {SAMPLE_COMPANY} team,</p>
                <p style="color:#374151; font-size:15px;">
                    Our daily scan found <strong>{len(SAMPLE_FINDINGS)} new security risks</strong> that need your attention:
                </p>
                <table style="width:100%; border-collapse:collapse; margin:16px 0; background:#fef2f2; border-radius:8px;">
                    {findings_html}
                </table>
                <div style="text-align:center; margin:24px 0;">
                    <a href="{DASHBOARD_URL}" style="background:#4f46e5; color:#fff; padding:14px 32px; 
                       border-radius:8px; text-decoration:none; font-weight:bold; font-size:15px;">
                        View my dashboard
                    </a>
                </div>
                <p style="color:#6b7280; font-size:13px;">
                    Our platform automatically fixes simple issues overnight.
                    Moderate issues include a step-by-step fix guide.
                    Critical issues are flagged for specialist review.
                </p>
            </div>
            {footer_html(SAMPLE_EMAIL)}
        </div>
    </body>
    </html>
    """


@router.get("/preview/weekly", response_class=HTMLResponse)
def preview_weekly_email():
    """Preview the weekly director summary email."""
    from services.email_service import footer_html, DASHBOARD_URL
    from datetime import datetime

    current_score = 68
    previous_score = 75
    score_change = current_score - previous_score
    score_color = "#dc2626"
    score_label = "High Risk"
    change_html = f'<span style="color:#16a34a;">▼ Down {abs(score_change)} points from last week</span>'
    change_note = "Good progress — your risk score has improved."

    actions_html = ""
    for i, action in enumerate(SAMPLE_ACTIONS, 1):
        actions_html += f"""
        <tr>
            <td style="padding:12px 16px; border-bottom:1px solid #f0f0f0;">
                <strong style="color:#111827;">{i}. {action.get('title')}</strong><br>
                <span style="color:#374151; font-size:14px;">{action.get('plain_english')}</span>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f9fafb; font-family: Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:32px 16px;">

            <div style="background:#fef3c7; border:1px solid #f59e0b; border-radius:8px;
                        padding:12px 16px; margin-bottom:16px; text-align:center;">
                <strong style="color:#92400e;">📧 EMAIL PREVIEW MODE — This is exactly what your clients will receive</strong>
            </div>

            <div style="background:#1e1b4b; border-radius:12px 12px 0 0; padding:24px 32px;">
                <h1 style="color:#fff; margin:0; font-size:22px;">
                    SecureIT360 <span style="color:#818cf8;">Weekly Summary</span>
                </h1>
                <p style="color:#a5b4fc; margin:4px 0 0 0; font-size:14px;">
                    by Global Cyber Assurance — {datetime.now().strftime("%A %d %B %Y")}
                </p>
            </div>

            <div style="background:#ffffff; padding:32px; border-left:1px solid #e5e7eb; border-right:1px solid #e5e7eb;">
                <p style="color:#111827; font-size:16px; margin-top:0;">Hi {SAMPLE_COMPANY} team,</p>
                <p style="color:#374151; font-size:15px;">Here is your weekly cyber security summary.</p>

                <div style="text-align:center; background:#f9fafb; border-radius:12px; padding:32px; margin:24px 0;">
                    <p style="color:#6b7280; font-size:14px; margin:0 0 8px 0;">Your Ransom Risk Score</p>
                    <div style="font-size:72px; font-weight:900; color:{score_color}; line-height:1;">{current_score}</div>
                    <div style="font-size:16px; color:{score_color}; font-weight:600; margin:4px 0;">{score_label}</div>
                    <div style="font-size:14px; margin-top:8px;">{change_html}</div>
                    <p style="color:#6b7280; font-size:13px; margin:8px 0 0 0;">{change_note}</p>
                </div>

                <h2 style="color:#111827; font-size:17px; margin:24px 0 12px 0;">Your top 3 actions this week</h2>
                <table style="width:100%; border-collapse:collapse; border-radius:8px; overflow:hidden; border:1px solid #e5e7eb;">
                    {actions_html}
                </table>

                <div style="text-align:center; margin:32px 0 16px 0;">
                    <a href="{DASHBOARD_URL}" style="background:#4f46e5; color:#fff; padding:14px 32px; 
                       border-radius:8px; text-decoration:none; font-weight:bold; font-size:15px;">
                        View my full dashboard
                    </a>
                </div>
            </div>
            {footer_html(SAMPLE_EMAIL)}
        </div>
    </body>
    </html>
    """


@router.get("/preview/monthly", response_class=HTMLResponse)
def preview_monthly_email():
    """Preview the monthly report email."""
    from services.email_service import footer_html, DASHBOARD_URL
    from datetime import datetime

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f9fafb; font-family: Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:32px 16px;">

            <div style="background:#fef3c7; border:1px solid #f59e0b; border-radius:8px;
                        padding:12px 16px; margin-bottom:16px; text-align:center;">
                <strong style="color:#92400e;">📧 EMAIL PREVIEW MODE — This is exactly what your clients will receive</strong>
            </div>

            <div style="background:#1e1b4b; border-radius:12px 12px 0 0; padding:24px 32px;">
                <h1 style="color:#fff; margin:0; font-size:22px;">
                    SecureIT360 <span style="color:#818cf8;">Monthly Report</span>
                </h1>
                <p style="color:#a5b4fc; margin:4px 0 0 0; font-size:14px;">
                    by Global Cyber Assurance — {datetime.now().strftime("%B %Y")}
                </p>
            </div>

            <div style="background:#ffffff; padding:32px; border-left:1px solid #e5e7eb; border-right:1px solid #e5e7eb;">
                <p style="color:#111827; font-size:16px; margin-top:0;">Hi {SAMPLE_COMPANY} team,</p>
                <p style="color:#374151; font-size:15px;">
                    Here is your monthly cyber security report for {datetime.now().strftime("%B %Y")}.
                </p>

                <div style="display:flex; gap:16px; margin:24px 0;">
                    <div style="flex:1; background:#f0fdf4; border-radius:8px; padding:20px; text-align:center;">
                        <div style="font-size:36px; font-weight:900; color:#16a34a;">5</div>
                        <div style="color:#374151; font-size:14px; margin-top:4px;">Issues fixed this month</div>
                    </div>
                    <div style="flex:1; background:#fef2f2; border-radius:8px; padding:20px; text-align:center;">
                        <div style="font-size:36px; font-weight:900; color:#dc2626;">12</div>
                        <div style="color:#374151; font-size:14px; margin-top:4px;">Total findings</div>
                    </div>
                    <div style="flex:1; background:#f0f9ff; border-radius:8px; padding:20px; text-align:center;">
                        <div style="font-size:36px; font-weight:900; color:#0284c7;">68</div>
                        <div style="color:#374151; font-size:14px; margin-top:4px;">Current risk score</div>
                    </div>
                </div>

                <div style="text-align:center; margin:32px 0 16px 0;">
                    <a href="{DASHBOARD_URL}" style="background:#4f46e5; color:#fff; padding:14px 32px;
                       border-radius:8px; text-decoration:none; font-weight:bold; font-size:15px;">
                        View full report
                    </a>
                </div>
            </div>
            {footer_html(SAMPLE_EMAIL)}
        </div>
    </body>
    </html>
    """


@router.get("/preview/improvement", response_class=HTMLResponse)
def preview_improvement_email():
    """Preview the score improvement email."""
    from services.email_service import footer_html, DASHBOARD_URL

    old_score = 75
    new_score = 45
    improvement = old_score - new_score

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#f9fafb; font-family: Arial, sans-serif;">
        <div style="max-width:600px; margin:0 auto; padding:32px 16px;">

            <div style="background:#fef3c7; border:1px solid #f59e0b; border-radius:8px;
                        padding:12px 16px; margin-bottom:16px; text-align:center;">
                <strong style="color:#92400e;">📧 EMAIL PREVIEW MODE — This is exactly what your clients will receive</strong>
            </div>

            <div style="background:#1e1b4b; border-radius:12px 12px 0 0; padding:24px 32px;">
                <h1 style="color:#fff; margin:0; font-size:22px;">
                    SecureIT360 <span style="color:#818cf8;">Good News</span>
                </h1>
                <p style="color:#a5b4fc; margin:4px 0 0 0; font-size:14px;">by Global Cyber Assurance</p>
            </div>

            <div style="background:#ffffff; padding:32px; border-left:1px solid #e5e7eb; border-right:1px solid #e5e7eb;">
                <p style="color:#111827; font-size:16px; margin-top:0;">Hi {SAMPLE_COMPANY} team,</p>
                <p style="color:#374151; font-size:15px;">Great news — your cyber security risk score has improved!</p>

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
                    <a href="{DASHBOARD_URL}" style="background:#16a34a; color:#fff; padding:14px 32px;
                       border-radius:8px; text-decoration:none; font-weight:bold; font-size:15px;">
                        View my dashboard
                    </a>
                </div>
            </div>
            {footer_html(SAMPLE_EMAIL)}
        </div>
    </body>
    </html>
    """