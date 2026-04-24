import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings

logger = logging.getLogger(__name__)

_BADGE_COLORS: dict[str, tuple[str, str]] = {
    "LOW":      ("#16a34a", "#dcfce7"),  # green text, green bg
    "MEDIUM":   ("#d97706", "#fef3c7"),  # amber text, amber bg
    "HIGH":     ("#dc2626", "#fee2e2"),  # red text, red bg
    "CRITICAL": ("#7f1d1d", "#fecaca"),  # dark-red text, red bg
}


def send_report_ready_email(
    to_email: str,
    first_name: str,
    legal_name: str,
    job_id: str,
    overall_score: int,
    risk_level: str,
    report_url: str,
) -> None:
    """Send an HTML + plaintext email via AWS SES when a compliance report is ready."""
    if not to_email:
        logger.warning("send_report_ready_email: no to_email for job %s, skipping", job_id)
        return

    text_color, bg_color = _BADGE_COLORS.get(risk_level.upper(), ("#374151", "#f3f4f6"))
    subject = f"Your Compliance Report for {legal_name} is Ready"

    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;padding:32px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:12px;border:1px solid #e5e7eb;overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="background:#1e3a5f;padding:28px 32px;">
              <p style="margin:0;color:#ffffff;font-size:20px;font-weight:700;">
                Compliance Audit Engine
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px;">
              <p style="margin:0 0 16px;font-size:15px;color:#111827;">
                Hi {first_name},
              </p>
              <p style="margin:0 0 24px;font-size:15px;color:#374151;line-height:1.6;">
                Your compliance report for <strong>{legal_name}</strong> has been completed and
                is now ready for review.
              </p>

              <!-- Score badge -->
              <table cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
                <tr>
                  <td style="background:{bg_color};border-radius:8px;padding:16px 24px;text-align:center;">
                    <p style="margin:0;font-size:13px;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">
                      Overall Compliance Score
                    </p>
                    <p style="margin:8px 0 4px;font-size:40px;font-weight:700;color:{text_color};">
                      {overall_score}
                    </p>
                    <p style="margin:0;font-size:14px;font-weight:600;color:{text_color};">
                      Risk Level: {risk_level}
                    </p>
                  </td>
                </tr>
              </table>

              <!-- CTA button -->
              <table cellpadding="0" cellspacing="0" style="margin:0 0 32px;">
                <tr>
                  <td style="background:#1d4ed8;border-radius:8px;">
                    <a href="{report_url}"
                       style="display:inline-block;padding:12px 28px;color:#ffffff;font-size:15px;
                              font-weight:600;text-decoration:none;">
                      View Full Report
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin:0;font-size:13px;color:#9ca3af;line-height:1.6;border-top:1px solid #f3f4f6;padding-top:20px;">
                <em>Disclaimer: This report is generated automatically for informational purposes only
                and does not constitute legal, financial, or regulatory advice. Always consult qualified
                professionals before making compliance decisions. Compliance Audit Engine does not
                warrant the accuracy or completeness of this report.</em>
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f9fafb;padding:16px 32px;border-top:1px solid #e5e7eb;">
              <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
                &copy; Compliance Audit Engine &bull; Job ID: {job_id}
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    text_body = f"""Hi {first_name},

Your compliance report for {legal_name} is ready.

Overall Compliance Score: {overall_score}
Risk Level: {risk_level}

View your full report here:
{report_url}

---
Disclaimer: This report is generated automatically for informational purposes only and does not
constitute legal, financial, or regulatory advice. Always consult qualified professionals before
making compliance decisions. Compliance Audit Engine does not warrant the accuracy or completeness
of this report.

Job ID: {job_id}
"""

    try:
        client = boto3.client("ses", region_name=settings.aws_region)
        client.send_email(
            Source=settings.from_email,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": text_body, "Charset": "UTF-8"},
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                },
            },
        )
        logger.info("Report-ready email sent to %s for job %s", to_email, job_id)
    except (ClientError, BotoCoreError) as exc:
        logger.warning("SES send_email failed for job %s: %s", job_id, exc)
