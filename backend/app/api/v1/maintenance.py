from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.maintenance_records import MaintenanceRecord
from app.models.users import User
from app.schemas.maintenance import (
    MaintenanceCreate, MaintenanceUpdate, MaintenanceResponse, MaintenanceCompleteRequest
)
from app.utils.pagination import PaginationParams
from app.utils.helpers import log_audit

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


@router.get("/", response_model=list[MaintenanceResponse])
async def list_maintenance(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List maintenance records."""
    result = await db.execute(
        select(MaintenanceRecord)
        .order_by(MaintenanceRecord.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    return result.scalars().all()


@router.post("/", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance(
    request: Request,
    maintenance_data: MaintenanceCreate,
    current_user: User = Depends(require_role("system_admin", "ict_technician")),
    db: AsyncSession = Depends(get_db),
):
    """Create a maintenance record."""
    record = MaintenanceRecord(
        **maintenance_data.model_dump(),
        performed_by_id=current_user.id,
    )
    db.add(record)
    await db.flush()

    await log_audit(
        db,
        action="create_maintenance",
        user_id=current_user.id,
        entity_type="maintenance",
        entity_id=record.id,
        details={"computer_id": maintenance_data.computer_id, "title": maintenance_data.title},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{record_id}", response_model=MaintenanceResponse)
async def get_maintenance(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a maintenance record by ID."""
    result = await db.execute(select(MaintenanceRecord).where(MaintenanceRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    return record


@router.put("/{record_id}", response_model=MaintenanceResponse)
async def update_maintenance(
    record_id: int,
    request: Request,
    update_data: MaintenanceUpdate,
    current_user: User = Depends(require_role("system_admin", "ict_technician")),
    db: AsyncSession = Depends(get_db),
):
    """Update a maintenance record."""
    result = await db.execute(select(MaintenanceRecord).where(MaintenanceRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(record, key, value)

    await log_audit(
        db,
        action="update_maintenance",
        user_id=current_user.id,
        entity_type="maintenance",
        entity_id=record_id,
        details=update_dict,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.post("/{record_id}/complete", response_model=MaintenanceResponse)
async def complete_maintenance(
    record_id: int,
    request: Request,
    complete_data: MaintenanceCompleteRequest,
    current_user: User = Depends(require_role("system_admin", "ict_technician")),
    db: AsyncSession = Depends(get_db),
):
    """Mark a maintenance record as completed."""
    result = await db.execute(select(MaintenanceRecord).where(MaintenanceRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    record.completed_date = complete_data.completed_date or date.today()
    if complete_data.notes:
        record.notes = complete_data.notes

    await log_audit(
        db,
        action="complete_maintenance",
        user_id=current_user.id,
        entity_type="maintenance",
        entity_id=record_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(record)
    return record
