from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.hardware_metrics import HardwareMetric
from app.models.alerts import Alert, AlertStatus
from app.models.users import User
from app.schemas.hardware import HardwareMetricResponse, ThresholdUpdate, ThresholdResponse
from app.schemas.alerts import AlertResponse
from app.utils.helpers import log_audit, get_setting
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/hardware", tags=["Hardware"])


@router.get("/metrics", response_model=list[HardwareMetricResponse])
async def get_latest_metrics(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest hardware metric per computer."""
    # Subquery to get max recorded_at per computer
    subq = (
        select(
            HardwareMetric.computer_id,
            func.max(HardwareMetric.recorded_at).label("max_recorded_at"),
        )
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
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    return result.scalars().all()


@router.get("/alerts", response_model=list[AlertResponse])
async def get_hardware_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all active hardware alerts."""
    result = await db.execute(
        select(Alert)
        .where(Alert.status == AlertStatus.active)
        .order_by(Alert.created_at.desc())
        .limit(200)
    )
    return result.scalars().all()


@router.get("/thresholds", response_model=ThresholdResponse)
async def get_thresholds(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current monitoring thresholds from system settings."""
    return ThresholdResponse(
        cpu_warning_percent=await get_setting(db, "cpu_warning_percent", 90.0),
        ram_warning_percent=await get_setting(db, "ram_warning_percent", 90.0),
        disk_warning_percent=await get_setting(db, "disk_warning_percent", 90.0),
        disk_critical_percent=await get_setting(db, "disk_critical_percent", 95.0),
        offline_timeout_minutes=await get_setting(db, "offline_timeout_minutes", 10),
        heartbeat_interval_seconds=await get_setting(db, "heartbeat_interval_seconds", 60),
        software_scan_interval_hours=await get_setting(db, "software_scan_interval_hours", 24),
        data_retention_days=await get_setting(db, "data_retention_days", 30),
    )


@router.put("/thresholds", response_model=ThresholdResponse)
async def update_thresholds(
    request: Request,
    update_data: ThresholdUpdate,
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update monitoring thresholds (admin only)."""
    from app.models.system_settings import SystemSetting

    updates = update_data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        )
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = str(value)
        else:
            setting = SystemSetting(
                key=key,
                value=str(value),
                value_type="float" if isinstance(value, float) else "integer",
                category="thresholds",
            )
            db.add(setting)

    await log_audit(
        db,
        action="update_thresholds",
        user_id=current_user.id,
        entity_type="system_settings",
        details=updates,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    # Return updated values
    return ThresholdResponse(
        cpu_warning_percent=await get_setting(db, "cpu_warning_percent", 90.0),
        ram_warning_percent=await get_setting(db, "ram_warning_percent", 90.0),
        disk_warning_percent=await get_setting(db, "disk_warning_percent", 90.0),
        disk_critical_percent=await get_setting(db, "disk_critical_percent", 95.0),
        offline_timeout_minutes=await get_setting(db, "offline_timeout_minutes", 10),
        heartbeat_interval_seconds=await get_setting(db, "heartbeat_interval_seconds", 60),
        software_scan_interval_hours=await get_setting(db, "software_scan_interval_hours", 24),
        data_retention_days=await get_setting(db, "data_retention_days", 30),
    )
