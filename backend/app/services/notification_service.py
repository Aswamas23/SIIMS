from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.notifications import Notification, NotificationType
from app.models.users import User, UserRole

logger = logging.getLogger(__name__)


async def create_notification(
    db: AsyncSession,
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    related_id: int = None,
    related_type: str = None,
) -> Notification:
    """Create an in-system notification for a user."""
    ntype = NotificationType(notification_type) if notification_type in NotificationType.__members__ else NotificationType.info

    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=ntype,
        related_id=related_id,
        related_type=related_type,
    )
    db.add(notification)
    return notification


async def notify_all_admins(
    db: AsyncSession,
    title: str,
    message: str,
    notification_type: str = "alert",
    related_id: int = None,
    related_type: str = None,
) -> None:
    """Send a notification to all active system administrators."""
    result = await db.execute(
        select(User).where(
            User.role == UserRole.system_admin,
            User.is_active == True,  # noqa
        )
    )
    admins = result.scalars().all()

    for admin in admins:
        await create_notification(
            db,
            user_id=admin.id,
            title=title,
            message=message,
            notification_type=notification_type,
            related_id=related_id,
            related_type=related_type,
        )

    logger.info(f"Notified {len(admins)} admin(s): {title}")


async def send_email_notification(
    to: str,
    subject: str,
    body: str,
    db: AsyncSession = None,
) -> bool:
    """Send an email notification. Uses DB SMTP settings if db is provided."""
    if db:
        from app.utils.email import send_email_from_db_settings
        return await send_email_from_db_settings(db=db, to=to, subject=subject, body=body)
    else:
        from app.utils.email import send_email
        return await send_email(to=to, subject=subject, body=body)
