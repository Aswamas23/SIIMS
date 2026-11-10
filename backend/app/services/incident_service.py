from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.incidents import Incident, IncidentCategory, IncidentSeverity, IncidentStatus
from app.models.alerts import Alert, AlertType

logger = logging.getLogger(__name__)


# Map AlertType to IncidentCategory
ALERT_TO_CATEGORY = {
    AlertType.cpu_high: IncidentCategory.performance,
    AlertType.ram_high: IncidentCategory.performance,
    AlertType.disk_high: IncidentCategory.hardware,
    AlertType.disk_critical: IncidentCategory.hardware,
    AlertType.smart_failure: IncidentCategory.hardware,
    AlertType.computer_offline: IncidentCategory.network,
    AlertType.network_issue: IncidentCategory.network,
    AlertType.licence_expiring: IncidentCategory.software,
    AlertType.licence_expired: IncidentCategory.software,
}

ALERT_SEVERITY_TO_INCIDENT_SEVERITY = {
    "warning": IncidentSeverity.medium,
    "critical": IncidentSeverity.critical,
    "info": IncidentSeverity.low,
}


async def auto_create_incident(
    db: AsyncSession,
    computer_id: int,
    alert: Alert,
) -> Incident | None:
    """
    Automatically create an incident from an alert.
    Avoids duplicates by checking for existing unresolved auto-created incidents
    with the same computer + category.
    """
    category = ALERT_TO_CATEGORY.get(alert.alert_type, IncidentCategory.other)
    severity = ALERT_SEVERITY_TO_INCIDENT_SEVERITY.get(str(alert.severity), IncidentSeverity.medium)

    # Check for existing unresolved auto-created incident for same computer + category
    existing = await db.execute(
        select(Incident).where(
            Incident.computer_id == computer_id,
            Incident.category == category,
            Incident.is_auto_created == True,  # noqa
            Incident.status.in_([IncidentStatus.open, IncidentStatus.in_progress]),
        )
    )
    if existing.scalar_one_or_none():
        logger.debug(f"Auto-incident already exists for computer {computer_id}, category {category}")
        return None

    # Generate incident number
    from app.utils.helpers import generate_incident_number
    incident_number = await generate_incident_number(db)

    incident = Incident(
        incident_number=incident_number,
        computer_id=computer_id,
        title=alert.title,
        description=f"Auto-created from alert: {alert.message}",
        category=category,
        severity=severity,
        status=IncidentStatus.open,
        is_auto_created=True,
        related_alert_id=alert.id,
    )
    db.add(incident)
    logger.info(f"Auto-created incident {incident_number} for computer {computer_id}")
    return incident
