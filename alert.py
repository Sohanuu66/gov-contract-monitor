"""
alert.py
Sends email alerts for new high-value government contracts.
All display config (columns, subject, source URL) is driven by config.py.
Uses SMTP with TLS — works with Gmail App Passwords out of the box.
"""

import os
import smtplib
import csv
import io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from config import (
    EMAIL_SUBJECT_TEMPLATE,
    AMOUNT_THRESHOLD_LABEL,
    SOURCE_URL,
    EMAIL_TABLE_COLUMNS,
    EMAIL_PLAIN_FIELDS,
    ENABLE_EXECUTIVE_SUMMARY,
    ENABLE_CSV_ATTACHMENT,
    CSV_ATTACHMENT_FILENAME,
    CSV_COLUMNS,
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


def _parse_amount_to_float(amount) -> float:
    try:
        return float(amount)
    except (TypeError, ValueError):
        return 0.0


def _generate_csv_data(awards: list[dict]) -> str:
    """Generate in-memory CSV string from awards."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator='\n')
    
    # Write headers
    headers = [col[0] for col in CSV_COLUMNS]
    writer.writerow(headers)
    
    # Write rows
    for award in awards:
        row = []
        for _, key in CSV_COLUMNS:
            val = award.get(key, "")
            if val is None:
                val = ""
            row.append(str(val))
        writer.writerow(row)
        
    return output.getvalue()


def _build_email_body(awards: list[dict]) -> tuple[str, str, str]:
    """Returns (subject, plain_text, html)."""
    count = len(awards)
    plural = "s" if count > 1 else ""
    subject = EMAIL_SUBJECT_TEMPLATE.format(
        count=count, plural=plural, threshold=AMOUNT_THRESHOLD_LABEL
    )

    # Calculate metrics
    amounts = [_parse_amount_to_float(a.get("Transaction Amount")) for a in awards]
    total_val = sum(amounts)
    largest_val = max(amounts) if amounts else 0.0
    avg_val = total_val / count if count > 0 else 0.0
    
    unique_companies = len(set(
        a.get("Recipient Name") 
        for a in awards 
        if a.get("Recipient Name") and a.get("Recipient Name") != "N/A"
    ))

    total_val_str = _format_amount(total_val)
    largest_val_str = _format_amount(largest_val)
    avg_val_str = _format_amount(avg_val)

    # ── Plain text ────────────────────────────────────────────────
    lines = [f"Found {count} new US government contract{plural} exceeding ${AMOUNT_THRESHOLD_LABEL}.\n"]
    
    if ENABLE_EXECUTIVE_SUMMARY:
        lines += [
            "Executive Summary:",
            "-" * 40,
            f"  Total Contracts     : {count}",
            f"  Total Value         : {total_val_str}",
            f"  Largest Contract    : {largest_val_str}",
            f"  Average Value       : {avg_val_str}",
            f"  Unique Companies    : {unique_companies}",
            "-" * 40,
            "\n"
        ]
        
    lines += ["=" * 60]
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
            f'<td style="padding:10px;border-bottom:1px solid #eee;'
            f'{"font-weight:bold;" if key == "Recipient Name" else ""}'
            f'{"color:#0a7c2b;font-weight:bold;" if key == "Transaction Amount" else ""}'
            f'">{_get_field(award, key)}</td>'
            for _, key in EMAIL_TABLE_COLUMNS
        )
        rows += f"<tr>{cells}</tr>"

    summary_html = ""
    if ENABLE_EXECUTIVE_SUMMARY:
        summary_html = f"""
      <div style="background:#f9f9f9; border-left:4px solid #b30000; padding:15px; margin-bottom:20px; border-radius:4px;">
        <h3 style="margin-top:0; color:#333;">Executive Summary</h3>
        <table style="width:100%; max-width:500px; font-size:14px; border-collapse:collapse;">
          <tr>
            <td style="padding:4px 0; color:#555;"><strong>Total Contracts:</strong></td>
            <td style="padding:4px 0; text-align:right; font-weight:bold;">{count}</td>
          </tr>
          <tr>
            <td style="padding:4px 0; color:#555;"><strong>Total Value:</strong></td>
            <td style="padding:4px 0; text-align:right; font-weight:bold; color:#0a7c2b;">{total_val_str}</td>
          </tr>
          <tr>
            <td style="padding:4px 0; color:#555;"><strong>Largest Contract:</strong></td>
            <td style="padding:4px 0; text-align:right; font-weight:bold; color:#0a7c2b;">{largest_val_str}</td>
          </tr>
          <tr>
            <td style="padding:4px 0; color:#555;"><strong>Average Value:</strong></td>
            <td style="padding:4px 0; text-align:right; font-weight:bold; color:#0a7c2b;">{avg_val_str}</td>
          </tr>
          <tr>
            <td style="padding:4px 0; color:#555;"><strong>Unique Companies:</strong></td>
            <td style="padding:4px 0; text-align:right; font-weight:bold;">{unique_companies}</td>
          </tr>
        </table>
      </div>
        """

    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#222">
      <h2 style="color:#b30000">🚨 {count} New US Gov Contract{plural} &gt; ${AMOUNT_THRESHOLD_LABEL}</h2>
      <p>The following contract{plural} {'were' if count > 1 else 'was'} awarded by the US Government.</p>
      {summary_html}
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

    # Sort awards by price (Transaction Amount) in descending order
    awards = sorted(
        awards,
        key=lambda a: _parse_amount_to_float(a.get("Transaction Amount")),
        reverse=True
    )

    subject, plain, html = _build_email_body(awards)

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)

    body_part = MIMEMultipart("alternative")
    body_part.attach(MIMEText(plain, "plain"))
    body_part.attach(MIMEText(html, "html"))
    msg.attach(body_part)

    if ENABLE_CSV_ATTACHMENT:
        csv_data = _generate_csv_data(awards)
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        filename = CSV_ATTACHMENT_FILENAME.format(date=date_str)
        
        attachment_part = MIMEBase("text", "csv")
        attachment_part.set_payload(csv_data.encode("utf-8"))
        encoders.encode_base64(attachment_part)
        attachment_part.add_header(
            "Content-Disposition",
            f'attachment; filename="{filename}"',
        )
        msg.attach(attachment_part)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipients, msg.as_string())

    print(f"[alert] Email sent to {recipients} — {len(awards)} contract(s).")