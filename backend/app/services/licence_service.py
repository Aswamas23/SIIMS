from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.software_licences import SoftwareLicence, LicenceStatus
from app.services.notification_service import notify_all_admins

logger = logging.getLogger(__name__)

# Days before expiry to send notifications
EXPIRY_NOTIFICATION_DAYS = [30, 14, 7, 0]


async def check_expiring_licences(db: AsyncSession) -> None:
    """
    Check for licences expiring within configured windows and send notifications.
    Prevents duplicate notifications for the same window period.
    """
    today = date.today()

    for days in EXPIRY_NOTIFICATION_DAYS:
        target_date = today + timedelta(days=days)

        result = await db.execute(
            select(SoftwareLicence).where(
                SoftwareLicence.expiry_date == target_date,
                SoftwareLicence.is_active == True,  # noqa
            )
        )
        licences = result.scalars().all()

        for licence in licences:
            if days == 0:
                title = f"Licence EXPIRED: {licence.software_name}"
                message = f"The licence for '{licence.software_name}' expired today ({target_date})."
                licence.status = LicenceStatus.expired
            else:
                title = f"Licence expiring in {days} days: {licence.software_name}"
                message = f"The licence for '{licence.software_name}' expires on {target_date} ({days} days from now)."
                licence.status = LicenceStatus.expiring_soon

            await notify_all_admins(
                db,
                title=title,
                message=message,
                notification_type="licence",
                related_id=licence.id,
                related_type="licence",
            )
            logger.info(f"Licence expiry notification: {licence.software_name}, {days} days")

    # Also update status for already-expired licences
    expired_result = await db.execute(
        select(SoftwareLicence).where(
            SoftwareLicence.expiry_date < today,
            SoftwareLicence.is_active == True,  # noqa
            SoftwareLicence.status != LicenceStatus.expired,
        )
    )
    for licence in expired_result.scalars().all():
        licence.status = LicenceStatus.expired

    await db.commit()
