from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from app.models.computers import Computer
from app.models.hardware_metrics import HardwareMetric
from app.models.alerts import Alert, AlertType, AlertSeverity, AlertStatus
from app.utils.helpers import get_setting

logger = logging.getLogger(__name__)


async def evaluate_hardware_metrics(db: AsyncSession) -> None:
    """
    Evaluate hardware metrics for all computers and create/update alerts
    when thresholds are exceeded.
    """
    # Get thresholds
    cpu_warn = await get_setting(db, "cpu_warning_percent", 90.0)
    ram_warn = await get_setting(db, "ram_warning_percent", 90.0)
    disk_warn = await get_setting(db, "disk_warning_percent", 90.0)
    disk_crit = await get_setting(db, "disk_critical_percent", 95.0)

    # Get the latest hardware metric per computer (last 5 minutes)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)

    # Get latest metric per computer
    subq = (
        select(
            HardwareMetric.computer_id,
            func.max(HardwareMetric.recorded_at).label("max_recorded_at"),
        )
        .where(HardwareMetric.recorded_at >= cutoff)
        .group_by(HardwareMetric.computer_id)
        .subquery()
    )

    result = await db.execute(
        select(HardwareMetric)
        .join(
            subq,
            (HardwareMetric.computer_id == subq.c.computer_id)
            & (HardwareMetric.recorded_at == subq.c.max_recorded_at),
        )
    )
    metrics = result.scalars().all()

    for metric in metrics:
        # Evaluate each metric against thresholds
        if metric.cpu_percent is not None:
            if metric.cpu_percent >= float(cpu_warn):
                await create_or_update_alert(
                    db,
                    computer_id=metric.computer_id,
                    alert_type=AlertType.cpu_high,
                    severity=AlertSeverity.warning,
                    title=f"High CPU usage: {metric.cpu_percent:.1f}%",
                    message=f"CPU usage is {metric.cpu_percent:.1f}%, threshold is {cpu_warn}%",
                    metric_value=metric.cpu_percent,
                    threshold_value=float(cpu_warn),
                )
            else:
                await resolve_alert_if_active(db, metric.computer_id, AlertType.cpu_high)

        if metric.ram_percent is not None:
            if metric.ram_percent >= float(ram_warn):
                await create_or_update_alert(
                    db,
                    computer_id=metric.computer_id,
                    alert_type=AlertType.ram_high,
                    severity=AlertSeverity.warning,
                    title=f"High RAM usage: {metric.ram_percent:.1f}%",
                    message=f"RAM usage is {metric.ram_percent:.1f}%, threshold is {ram_warn}%",
                    metric_value=metric.ram_percent,
                    threshold_value=float(ram_warn),
                )
            else:
                await resolve_alert_if_active(db, metric.computer_id, AlertType.ram_high)

        if metric.disk_percent is not None:
            if metric.disk_percent >= float(disk_crit):
                await create_or_update_alert(
                    db,
                    computer_id=metric.computer_id,
                    alert_type=AlertType.disk_critical,
                    severity=AlertSeverity.critical,
                    title=f"Critical disk usage: {metric.disk_percent:.1f}%",
                    message=f"Disk usage is {metric.disk_percent:.1f}%, critical threshold is {disk_crit}%",
                    metric_value=metric.disk_percent,
                    threshold_value=float(disk_crit),
                )
                # Auto-create incident for critical disk
                from app.services.incident_service import auto_create_incident
                alert = await _get_active_alert(db, metric.computer_id, AlertType.disk_critical)
                if alert:
                    await auto_create_incident(db, metric.computer_id, alert)
            elif metric.disk_percent >= float(disk_warn):
                await create_or_update_alert(
                    db,
                    computer_id=metric.computer_id,
                    alert_type=AlertType.disk_high,
                    severity=AlertSeverity.warning,
                    title=f"High disk usage: {metric.disk_percent:.1f}%",
                    message=f"Disk usage is {metric.disk_percent:.1f}%, threshold is {disk_warn}%",
                    metric_value=metric.disk_percent,
                    threshold_value=float(disk_warn),
                )
            else:
                await resolve_alert_if_active(db, metric.computer_id, AlertType.disk_high)
                await resolve_alert_if_active(db, metric.computer_id, AlertType.disk_critical)

        if metric.smart_status and metric.smart_status.lower() in ("failing", "failed"):
            await create_or_update_alert(
                db,
                computer_id=metric.computer_id,
                alert_type=AlertType.smart_failure,
                severity=AlertSeverity.critical,
                title="SMART disk failure detected",
                message=f"Disk SMART status: {metric.smart_status}",
                metric_value=None,
                threshold_value=None,
            )

    await db.commit()


async def create_or_update_alert(
    db: AsyncSession,
    computer_id: int,
    alert_type: AlertType,
    severity: AlertSeverity,
    title: str,
    message: str,
    metric_value: float = None,
    threshold_value: float = None,
) -> Alert:
    """
    Create a new alert or update the existing active alert of the same type.
    Alert deduplication: only one active alert per computer + type at a time.
    """
    existing = await db.execute(
        select(Alert).where(
            Alert.computer_id == computer_id,
            Alert.alert_type == alert_type,
            Alert.status == AlertStatus.active,
        )
    )
    alert = existing.scalar_one_or_none()

    if alert:
        # Update the existing alert
        alert.metric_value = metric_value
        alert.severity = severity
    else:
        # Create a new alert
        alert = Alert(
            computer_id=computer_id,
            alert_type=alert_type,
            severity=severity,
            status=AlertStatus.active,
            title=title,
            message=message,
            metric_value=metric_value,
            threshold_value=threshold_value,
        )
        db.add(alert)
        logger.info(f"New alert created: {alert_type} for computer {computer_id}")

    return alert


async def resolve_alert_if_active(
    db: AsyncSession,
    computer_id: int,
    alert_type: AlertType,
) -> None:
    """Resolve an active alert when the metric returns to normal."""
    existing = await db.execute(
        select(Alert).where(
            Alert.computer_id == computer_id,
            Alert.alert_type == alert_type,
            Alert.status == AlertStatus.active,
        )
    )
    alert = existing.scalar_one_or_none()
    if alert:
        alert.status = AlertStatus.resolved
        alert.resolved_at = datetime.now(timezone.utc)
        logger.info(f"Alert resolved: {alert_type} for computer {computer_id}")

        # Send recovery notification
        await send_recovery_notification(db, alert)


async def _get_active_alert(
    db: AsyncSession, computer_id: int, alert_type: AlertType
) -> Alert | None:
    result = await db.execute(
        select(Alert).where(
            Alert.computer_id == computer_id,
            Alert.alert_type == alert_type,
            Alert.status == AlertStatus.active,
        )
    )
    return result.scalar_one_or_none()


async def send_recovery_notification(db: AsyncSession, alert: Alert) -> None:
    """Send a notification when an alert is resolved."""
    from app.services.notification_service import notify_all_admins

    await notify_all_admins(
        db,
        title=f"Alert resolved: {alert.title}",
        message=f"The alert '{alert.title}' for computer ID {alert.computer_id} has been automatically resolved.",
        notification_type="alert",
        related_id=alert.id,
    )
