import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(
    to: str,
    subject: str,
    body: str,
    html_body: str = None,
    smtp_host: str = None,
    smtp_port: int = None,
    smtp_user: str = None,
    smtp_password: str = None,
    smtp_from: str = None,
) -> bool:
    """
    Send an email using aiosmtplib.
    Falls back to settings env vars if SMTP params not provided.
    Returns True on success, False on failure.
    """
    host = smtp_host or settings.SMTP_HOST
    port = smtp_port or settings.SMTP_PORT
    user = smtp_user or settings.SMTP_USER
    password = smtp_password or settings.SMTP_PASSWORD
    from_addr = smtp_from or settings.SMTP_FROM

    if not host or not user:
        logger.warning("SMTP not configured — email not sent")
        return False

    # Build the message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to

    text_part = MIMEText(body, "plain")
    msg.attach(text_part)

    if html_body:
        html_part = MIMEText(html_body, "html")
        msg.attach(html_part)

    try:
        await aiosmtplib.send(
            msg,
            hostname=host,
            port=port,
            username=user,
            password=password,
            start_tls=True,
        )
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False


async def send_email_from_db_settings(
    db,
    to: str,
    subject: str,
    body: str,
    html_body: str = None,
) -> bool:
    """Send email using SMTP settings stored in system_settings table."""
    from app.utils.helpers import get_setting
    from app.core.security import decrypt_value

    smtp_host = await get_setting(db, "smtp_host", settings.SMTP_HOST)
    smtp_port = await get_setting(db, "smtp_port", settings.SMTP_PORT)
    smtp_user = await get_setting(db, "smtp_user", settings.SMTP_USER)
    smtp_password_enc = await get_setting(db, "smtp_password_encrypted", "")
    smtp_from = await get_setting(db, "smtp_from", settings.SMTP_FROM)

    # Decrypt password
    smtp_password = decrypt_value(smtp_password_enc) if smtp_password_enc else settings.SMTP_PASSWORD

    return await send_email(
        to=to,
        subject=subject,
        body=body,
        html_body=html_body,
        smtp_host=smtp_host,
        smtp_port=int(smtp_port) if smtp_port else None,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        smtp_from=smtp_from,
    )
