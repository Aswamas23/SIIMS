from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
import logging

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _job_evaluate_hardware():
    """Job: evaluate hardware metrics and create/update alerts."""
    async with AsyncSessionLocal() as db:
        try:
            from app.services.alert_service import evaluate_hardware_metrics
            await evaluate_hardware_metrics(db)
        except Exception as e:
            logger.error(f"Error in evaluate_hardware_metrics job: {e}", exc_info=True)


async def _job_mark_computers_offline():
    """Job: mark computers offline if they haven't sent a heartbeat."""
    async with AsyncSessionLocal() as db:
        try:
            from app.services.computer_service import mark_computers_offline
            count = await mark_computers_offline(db)
            if count > 0:
                logger.info(f"Marked {count} computer(s) offline")
        except Exception as e:
            logger.error(f"Error in mark_computers_offline job: {e}", exc_info=True)


async def _job_check_expiring_licences():
    """Job: check for expiring software licences."""
    async with AsyncSessionLocal() as db:
        try:
            from app.services.licence_service import check_expiring_licences
            await check_expiring_licences(db)
        except Exception as e:
            logger.error(f"Error in check_expiring_licences job: {e}", exc_info=True)


async def _job_prune_old_data():
    """Job: delete old metrics data beyond the retention period."""
    async with AsyncSessionLocal() as db:
        try:
            from app.utils.helpers import get_setting
            from app.models.hardware_metrics import HardwareMetric
            from app.models.network_metrics import NetworkMetric
            from sqlalchemy import delete

            retention_days = await get_setting(db, "data_retention_days", 30)
            cutoff = datetime.now(timezone.utc) - timedelta(days=int(retention_days))

            hw_result = await db.execute(
                delete(HardwareMetric).where(HardwareMetric.recorded_at < cutoff)
            )
            net_result = await db.execute(
                delete(NetworkMetric).where(NetworkMetric.recorded_at < cutoff)
            )
            await db.commit()
            logger.info(
                f"Pruned old data: {hw_result.rowcount} hardware metrics, "
                f"{net_result.rowcount} network metrics (retention: {retention_days} days)"
            )
        except Exception as e:
            logger.error(f"Error in prune_old_data job: {e}", exc_info=True)


def setup_scheduler():
    """Register all scheduled jobs and return the scheduler."""
    # Evaluate hardware metrics every 1 minute
    scheduler.add_job(
        _job_evaluate_hardware,
        trigger=IntervalTrigger(minutes=1),
        id="evaluate_hardware",
        replace_existing=True,
        max_instances=1,
    )

    # Mark computers offline every 5 minutes
    scheduler.add_job(
        _job_mark_computers_offline,
        trigger=IntervalTrigger(minutes=5),
        id="mark_computers_offline",
        replace_existing=True,
        max_instances=1,
    )

    # Check expiring licences daily at 08:00
    scheduler.add_job(
        _job_check_expiring_licences,
        trigger=CronTrigger(hour=8, minute=0),
        id="check_expiring_licences",
        replace_existing=True,
        max_instances=1,
    )

    # Prune old data daily at 02:00
    scheduler.add_job(
        _job_prune_old_data,
        trigger=CronTrigger(hour=2, minute=0),
        id="prune_old_data",
        replace_existing=True,
        max_instances=1,
    )

    return scheduler
