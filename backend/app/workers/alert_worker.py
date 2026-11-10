"""
Alert worker — thin wrapper around alert_service.
Called by the scheduler job.
"""
from app.core.database import AsyncSessionLocal
from app.services.alert_service import evaluate_hardware_metrics
import logging

logger = logging.getLogger(__name__)


async def run_alert_evaluation():
    """Open a DB session and run hardware metric evaluation."""
    async with AsyncSessionLocal() as db:
        try:
            await evaluate_hardware_metrics(db)
        except Exception as e:
            logger.error(f"Alert evaluation failed: {e}", exc_info=True)
