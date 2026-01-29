"""Email notification client using SMTP."""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from typing import TYPE_CHECKING, Any, Optional

from tsc.config import get_settings

if TYPE_CHECKING:
    from tsc.parsers.models import ParsedBook
    from tsc.processors.concept_extractor import ExtractedConcept
    from tsc.processors.action_extractor import ExtractedAction


class EmailClient:
    """SMTP email client for notifications."""

    def __init__(self):
        """Initialize email client with configured credentials."""
        settings = get_settings()

        if not settings.smtp_user or not settings.smtp_password:
            raise ValueError(
                "SMTP credentials not configured. "
                "Please set SMTP_USER and SMTP_PASSWORD in config.env"
            )

        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self.recipient = settings.tsc_email_to or settings.smtp_user

    def send(self, subject: str, body_html: str, body_text: Optional[str] = None) -> bool:
        """Send an email.

        Args:
            subject: Email subject line.
            body_html: HTML body content.
            body_text: Optional plain text body (fallback).

        Returns:
            True if sent successfully, False otherwise.
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.user
        msg["To"] = self.recipient

        # Add plain text version
        if body_text:
            msg.attach(MIMEText(body_text, "plain"))

        # Add HTML version
        msg.attach(MIMEText(body_html, "html"))

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.user, self.recipient, msg.as_string())
            return True
        except Exception as e:
            print(f"Warning: Failed to send email: {e}")
            return False


def _build_book_processed_email(
    book: "ParsedBook",
    concepts: list[Any],
    actions: list[Any],
    asana_urls: dict[str, str],
) -> tuple[str, str]:
    """Build email content for a processed book.

    Returns:
        Tuple of (subject, html_body).
    """
    counts = book.highlight_counts()
    total = sum(counts.values())

    subject = f"📚 TSC: Processed \"{book.metadata.title}\""

    # Build concepts list
    concepts_html = ""
    if concepts:
        concept_items = "\n".join(
            f"<li><strong>{c.name}</strong> — {c.description}</li>"
            for c in concepts
        )
        concepts_html = f"""
        <h3>Key Concepts ({len(concepts)})</h3>
        <ul>{concept_items}</ul>
        """

    # Build actions list
    actions_html = ""
    if actions:
        action_items = []
        for a in actions:
            url = asana_urls.get(a.title, "")
            link = f' <a href="{url}">[Asana]</a>' if url else ""
            action_items.append(f"<li>{a.title}{link}</li>")
        actions_html = f"""
        <h3>Action Items ({len(actions)})</h3>
        <ul>{"".join(action_items)}</ul>
        """

    html_body = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #2d3748;">📚 Book Processed</h1>

        <div style="background: #f7fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="margin-top: 0; color: #4a5568;">{book.metadata.title}</h2>
            <p style="color: #718096; margin-bottom: 0;">by {book.metadata.author}</p>
        </div>

        <div style="margin-bottom: 20px;">
            <h3>Highlight Summary</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">🟡 Concepts (Yellow)</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;"><strong>{counts['yellow']}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">🩷 Actions (Pink)</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;"><strong>{counts['pink']}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">🔵 Quotes (Blue)</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;"><strong>{counts['blue']}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">🟠 Disagreements (Orange)</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;"><strong>{counts['orange']}</strong></td>
                </tr>
                <tr style="background: #edf2f7;">
                    <td style="padding: 8px;"><strong>Total</strong></td>
                    <td style="padding: 8px; text-align: right;"><strong>{total}</strong></td>
                </tr>
            </table>
        </div>

        {concepts_html}
        {actions_html}

        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
        <p style="color: #a0aec0; font-size: 12px;">
            Generated by The Silent Cartographer<br>
            {date.today().isoformat()}
        </p>
    </body>
    </html>
    """

    return subject, html_body


async def send_notification(
    book: "ParsedBook",
    concepts: list[Any],
    actions: list[Any],
    asana_urls: dict[str, str],
) -> bool:
    """Send notification email for a processed book.

    Args:
        book: The processed book.
        concepts: Extracted concepts.
        actions: Extracted actions.
        asana_urls: Mapping of action titles to Asana URLs.

    Returns:
        True if email sent successfully.
    """
    try:
        client = EmailClient()
        subject, body = _build_book_processed_email(book, concepts, actions, asana_urls)
        return client.send(subject, body)
    except ValueError as e:
        print(f"Warning: Email not configured: {e}")
        return False
