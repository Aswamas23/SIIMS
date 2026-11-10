from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.incidents import Incident, IncidentStatus
from app.models.incident_updates import IncidentUpdate, UpdateType
from app.models.users import User
from app.schemas.incidents import (
    IncidentCreate, IncidentUpdate as IncidentUpdateSchema,
    IncidentAssignRequest, IncidentUpdateCreate,
    IncidentResolveRequest, IncidentResponse
)
from app.utils.pagination import PaginationParams
from app.utils.helpers import log_audit, generate_incident_number

router = APIRouter(prefix="/incidents", tags=["Incidents"])


def _load_incident_query():
    return select(Incident).options(selectinload(Incident.updates))


@router.get("/", response_model=list[IncidentResponse])
async def list_incidents(
    pagination: PaginationParams = Depends(),
    inc_status: str = Query(None, alias="status"),
    severity: str = Query(None),
    computer_id: int = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List incidents with optional filters."""
    query = _load_incident_query()

    if inc_status:
        query = query.where(Incident.status == inc_status)
    if severity:
        query = query.where(Incident.severity == severity)
    if computer_id:
        query = query.where(Incident.computer_id == computer_id)

    result = await db.execute(
        query.order_by(Incident.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    return result.scalars().all()


@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    request: Request,
    incident_data: IncidentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new incident."""
    incident_number = await generate_incident_number(db)
    incident = Incident(
        incident_number=incident_number,
        computer_id=incident_data.computer_id,
        title=incident_data.title,
        description=incident_data.description,
        category=incident_data.category,
        severity=incident_data.severity,
        created_by_id=current_user.id,
    )
    db.add(incident)
    await db.flush()

    await log_audit(
        db,
        action="create_incident",
        user_id=current_user.id,
        entity_type="incident",
        entity_id=incident.id,
        details={"incident_number": incident_number, "title": incident.title},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    result = await db.execute(
        _load_incident_query().where(Incident.id == incident.id)
    )
    return result.scalar_one()


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get an incident by ID including its updates."""
    result = await db.execute(
        _load_incident_query().where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: int,
    request: Request,
    update_data: IncidentUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an incident."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    old_status = incident.status

    for key, value in update_dict.items():
        setattr(incident, key, value)

    # Add status change update if status changed
    if "status" in update_dict and update_dict["status"] != old_status:
        status_update = IncidentUpdate(
            incident_id=incident_id,
            user_id=current_user.id,
            update_type=UpdateType.status_change,
            message=f"Status changed from {old_status} to {update_dict['status']}",
            old_status=str(old_status),
            new_status=str(update_dict["status"]),
        )
        db.add(status_update)

    await log_audit(
        db,
        action="update_incident",
        user_id=current_user.id,
        entity_type="incident",
        entity_id=incident_id,
        details=update_dict,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    result = await db.execute(_load_incident_query().where(Incident.id == incident_id))
    return result.scalar_one()


@router.post("/{incident_id}/assign")
async def assign_incident(
    incident_id: int,
    request: Request,
    assign_data: IncidentAssignRequest,
    current_user: User = Depends(require_role("system_admin", "ict_technician")),
    db: AsyncSession = Depends(get_db),
):
    """Assign an incident to a user."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.assigned_to_id = assign_data.user_id
    incident.status = IncidentStatus.in_progress

    update = IncidentUpdate(
        incident_id=incident_id,
        user_id=current_user.id,
        update_type=UpdateType.assignment,
        message=f"Incident assigned to user ID {assign_data.user_id}",
    )
    db.add(update)

    await log_audit(
        db,
        action="assign_incident",
        user_id=current_user.id,
        entity_type="incident",
        entity_id=incident_id,
        details={"assigned_to": assign_data.user_id},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": "Incident assigned"}


@router.post("/{incident_id}/update")
async def add_incident_update(
    incident_id: int,
    update_data: IncidentUpdateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a comment or update to an incident."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    update = IncidentUpdate(
        incident_id=incident_id,
        user_id=current_user.id,
        update_type=update_data.update_type,
        message=update_data.message,
    )
    db.add(update)
    await db.commit()
    return {"message": "Update added"}


@router.post("/{incident_id}/resolve")
async def resolve_incident(
    incident_id: int,
    request: Request,
    resolve_data: IncidentResolveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark an incident as resolved."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = IncidentStatus.resolved
    incident.resolved_at = datetime.now(timezone.utc)
    incident.resolution_notes = resolve_data.resolution_notes

    update = IncidentUpdate(
        incident_id=incident_id,
        user_id=current_user.id,
        update_type=UpdateType.resolution,
        message=resolve_data.resolution_notes or "Incident resolved",
        old_status="open",
        new_status="resolved",
    )
    db.add(update)

    await log_audit(
        db,
        action="resolve_incident",
        user_id=current_user.id,
        entity_type="incident",
        entity_id=incident_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": "Incident resolved"}


@router.post("/{incident_id}/close")
async def close_incident(
    incident_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Close a resolved incident."""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = IncidentStatus.closed

    update = IncidentUpdate(
        incident_id=incident_id,
        user_id=current_user.id,
        update_type=UpdateType.status_change,
        message="Incident closed",
        new_status="closed",
    )
    db.add(update)

    await log_audit(
        db,
        action="close_incident",
        user_id=current_user.id,
        entity_type="incident",
        entity_id=incident_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": "Incident closed"}
