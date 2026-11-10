from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


def now_utc() -> datetime:
    """Return the current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


async def generate_incident_number(db: AsyncSession) -> str:
    """Generate a unique incident number in format INC-YYYYMMDD-NNNN."""
    from app.models.incidents import Incident

    today = now_utc().strftime("%Y%m%d")
    prefix = f"INC-{today}-"

    # Count incidents created today
    result = await db.execute(
        select(func.count(Incident.id)).where(
            Incident.incident_number.like(f"{prefix}%")
        )
    )
    count = result.scalar_one() or 0
    return f"{prefix}{(count + 1):04d}"


def truncate_string(text: str, max_length: int = 255) -> str:
    """Truncate a string to max_length, appending '...' if truncated."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


async def get_setting(db: AsyncSession, key: str, default=None):
    """Retrieve a system setting value by key with type coercion."""
    from app.models.system_settings import SystemSetting

    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    )
    setting = result.scalar_one_or_none()
    if setting is None:
        return default

    value = setting.value
    if value is None:
        return default

    # Coerce based on declared type
    try:
        if setting.value_type == "integer":
            return int(value)
        elif setting.value_type == "float":
            return float(value)
        elif setting.value_type == "boolean":
            return value.lower() in ("true", "1", "yes")
        else:
            return value
    except (ValueError, TypeError):
        return default


async def log_audit(
    db: AsyncSession,
    action: str,
    user_id: int = None,
    entity_type: str = None,
    entity_id: int = None,
    details: dict = None,
    ip_address: str = None,
    user_agent: str = None,
) -> None:
    """Create an audit log entry."""
    from app.models.audit_logs import AuditLog

    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log)
    # Caller is responsible for committing
