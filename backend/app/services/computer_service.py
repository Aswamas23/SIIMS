from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.computers import Computer, ComputerStatus
from app.models.alerts import Alert, AlertType, AlertSeverity, AlertStatus
from app.utils.helpers import get_setting

logger = logging.getLogger(__name__)


async def mark_computers_offline(db: AsyncSession) -> int:
    """
    Mark computers as OFFLINE if they haven't sent a heartbeat within the timeout.
    Returns the number of computers marked offline.
    """
    offline_timeout_minutes = await get_setting(db, "offline_timeout_minutes", 10)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=offline_timeout_minutes)

    result = await db.execute(
        select(Computer).where(
            Computer.is_active == True,  # noqa
            Computer.last_seen.isnot(None),
            Computer.last_seen < cutoff,
            Computer.status != ComputerStatus.offline,
        )
    )
    computers = result.scalars().all()

    count = 0
    for computer in computers:
        previous_status = computer.status
        computer.status = ComputerStatus.offline
        count += 1

        # Create offline alert (deduplicated)
        await _create_offline_alert(db, computer)
        logger.info(f"Computer {computer.hostname} marked offline (was {previous_status})")

    if count > 0:
        await db.commit()

    return count


async def _create_offline_alert(db: AsyncSession, computer: Computer) -> None:
    """Create an OFFLINE alert if one doesn't already exist."""
    existing = await db.execute(
        select(Alert).where(
            Alert.computer_id == computer.id,
            Alert.alert_type == AlertType.computer_offline,
            Alert.status == AlertStatus.active,
        )
    )
    if existing.scalar_one_or_none():
        return  # Already has an active offline alert

    alert = Alert(
        computer_id=computer.id,
        alert_type=AlertType.computer_offline,
        severity=AlertSeverity.critical,
        status=AlertStatus.active,
        title=f"{computer.hostname} is offline",
        message=f"Computer has not sent a heartbeat since {computer.last_seen}",
    )
    db.add(alert)
