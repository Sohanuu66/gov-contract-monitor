"""
alert.py
Sends email alerts for new high-value government contracts.
All display config (columns, subject, source URL) is driven by config.py.
Uses SMTP with TLS — works with Gmail App Passwords out of the box.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import (
    EMAIL_SUBJECT_TEMPLATE,
    AMOUNT_THRESHOLD_LABEL,
    SOURCE_URL,
    EMAIL_TABLE_COLUMNS,
    EMAIL_PLAIN_FIELDS,
)


def _format_amount(amount) -> str:
    try:
        return f"${float(amount):,.0f}"
    except (TypeError, ValueError):
        return str(amount)


def _get_field(award: dict, key: str) -> str:
    val = award.get(key, "N/A")
    if key == "Transaction Amount":
        return _format_amount(val)
    return str(val) if val else "N/A"


def _build_email_body(awards: list[dict]) -> tuple[str, str, str]:
    """Returns (subject, plain_text, html)."""
    count = len(awards)
    plural = "s" if count > 1 else ""
    subject = EMAIL_SUBJECT_TEMPLATE.format(
        count=count, plural=plural, threshold=AMOUNT_THRESHOLD_LABEL
    )

    # ── Plain text ────────────────────────────────────────────────
    lines = [f"Found {count} new US government contract{plural} exceeding ${AMOUNT_THRESHOLD_LABEL}.\n", "=" * 60]
    for i, award in enumerate(awards, 1):
        lines.append(f"\n#{i}")
        for label, key in EMAIL_PLAIN_FIELDS:
            lines.append(f"  {label:<14}: {_get_field(award, key)}")
    lines += ["\n" + "=" * 60, f"Source: {SOURCE_URL}"]
    plain = "\n".join(lines)

    # ── HTML ──────────────────────────────────────────────────────
    headers = "".join(
        f'<th style="padding:10px;text-align:left;background:#f0f0f0">{label}</th>'
        for label, _ in EMAIL_TABLE_COLUMNS
    )

    rows = ""
    for award in awards:
        cells = "".join(
            f'<td style="padding:10px;border-bottom:1px solid #eee'
            f'{"font-weight:bold" if key == "Recipient Name" else ""}'
            f'{"color:#0a7c2b;font-weight:bold" if key == "Transaction Amount" else ""}'
            f'">{_get_field(award, key)}</td>'
            for _, key in EMAIL_TABLE_COLUMNS
        )
        rows += f"<tr>{cells}</tr>"

    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#222">
      <h2 style="color:#b30000">🚨 {count} New US Gov Contract{plural} &gt; ${AMOUNT_THRESHOLD_LABEL}</h2>
      <p>The following contract{plural} {'were' if count > 1 else 'was'} awarded by the US Government.</p>
      <table style="border-collapse:collapse;width:100%;font-size:14px">
        <thead><tr>{headers}</tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <br>
      <p style="font-size:12px;color:#888">
        Source: <a href="{SOURCE_URL}">{SOURCE_URL}</a> |
        Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
      </p>
    </body></html>"""

    return subject, plain, html


def send_alert(awards: list[dict]) -> None:
    """
    Send email alert. Reads SMTP config from environment variables:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_TO
    """
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    recipients = [r.strip() for r in os.environ["ALERT_TO"].split(",")]

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