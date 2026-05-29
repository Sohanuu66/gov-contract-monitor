"""
alert.py
Sends email alerts for new high-value government contracts.
Uses SMTP with TLS — works with Gmail App Passwords out of the box.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


def _format_amount(amount) -> str:
    try:
        return f"${float(amount):,.0f}"
    except (TypeError, ValueError):
        return str(amount)


def _build_email_body(awards: list[dict]) -> tuple[str, str, str]:
    """Returns (subject, plain_text, html) for the alert email."""
    count = len(awards)
    subject = f"🚨 {count} New US Gov Contract{'s' if count > 1 else ''} > $50M"

    # ── Plain text ──────────────────────────────────────────────────────────
    lines = [
        f"Found {count} new US government contract{'s' if count > 1 else ''} exceeding $50M.\n",
        "=" * 60,
    ]
    for i, award in enumerate(awards, 1):
        lines += [
            f"\n#{i}",
            f"  Company     : {award.get('Recipient Name', 'N/A')}",
            f"  Amount      : {_format_amount(award.get('Transaction Amount'))}",
            f"  Action Date : {award.get('Action Date', 'N/A')}",
            f"  Award ID    : {award.get('Award ID', 'N/A')}",
            f"  Agency      : {award.get('Awarding Agency', 'N/A')}",
            f"  Sub-Agency  : {award.get('Awarding Sub Agency', 'N/A')}",
            f"  Type        : {award.get('Award Type', 'N/A')}",
            f"  Description : {award.get('Transaction Description', 'N/A')}",
        ]
    lines += ["\n" + "=" * 60, "Source: https://www.usaspending.gov"]
    plain = "\n".join(lines)

    # ── HTML ────────────────────────────────────────────────────────────────
    rows = ""
    for award in awards:
        rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #eee;font-weight:bold">
            {award.get('Recipient Name', 'N/A')}
          </td>
          <td style="padding:10px;border-bottom:1px solid #eee;color:#0a7c2b;font-weight:bold">
            {_format_amount(award.get('Transaction Amount'))}
          </td>
          <td style="padding:10px;border-bottom:1px solid #eee">
            {award.get('Action Date', 'N/A')}
          </td>
          <td style="padding:10px;border-bottom:1px solid #eee">
            {award.get('Award ID', 'N/A')}
          </td>
          <td style="padding:10px;border-bottom:1px solid #eee">
            {award.get('Awarding Agency', 'N/A')}
          </td>
          <td style="padding:10px;border-bottom:1px solid #eee">
            {award.get('Award Type', 'N/A')}
          </td>
        </tr>"""

    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#222">
      <h2 style="color:#b30000">🚨 {count} New US Gov Contract{'s' if count > 1 else ''} &gt; $50M</h2>
      <p>The following contract{'s were' if count > 1 else ' was'} awarded by the US Government
         and flagged by the automated monitor.</p>
      <table style="border-collapse:collapse;width:100%;font-size:14px">
        <thead>
          <tr style="background:#f0f0f0">
            <th style="padding:10px;text-align:left">Company</th>
            <th style="padding:10px;text-align:left">Amount</th>
            <th style="padding:10px;text-align:left">Action Date</th>
            <th style="padding:10px;text-align:left">Award ID</th>
            <th style="padding:10px;text-align:left">Agency</th>
            <th style="padding:10px;text-align:left">Type</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <br>
      <p style="font-size:12px;color:#888">
        Source: <a href="https://www.usaspending.gov">usaspending.gov</a> |
        Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
      </p>
    </body></html>"""

    return subject, plain, html


def send_alert(awards: list[dict]) -> None:
    """
    Send an email alert for the given awards.
    Reads config from environment variables:
      SMTP_HOST     — e.g. smtp.gmail.com
      SMTP_PORT     — e.g. 587
      SMTP_USER     — sender email address
      SMTP_PASSWORD — app password (not account password)
      ALERT_TO      — recipient email (comma-separated for multiple)
    """
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    alert_to = os.environ["ALERT_TO"]

    recipients = [r.strip() for r in alert_to.split(",")]
    subject, plain, html = _build_email_body(awards)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipients, msg.as_string())

    print(f"[alert] Email sent to {recipients} — {len(awards)} contract(s).")