"""
Notification worker — thin wrapper around notification_service.
Can be used for batch notification dispatch in future.
"""
from app.core.database import AsyncSessionLocal
from app.services.notification_service import notify_all_admins
import logging

logger = logging.getLogger(__name__)


async def dispatch_notification(title: str, message: str, notification_type: str = "system"):
    """Dispatch a notification to all admins from a background context."""
    async with AsyncSessionLocal() as db:
        try:
            await notify_all_admins(
                db,
                title=title,
                message=message,
                notification_type=notification_type,
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Notification dispatch failed: {e}", exc_info=True)
