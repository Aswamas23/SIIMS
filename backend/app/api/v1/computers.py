import secrets
from fastapi import APIRouter, Depends, HTTPException, status as http_status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.security import hash_password
from app.models.computers import Computer
from app.models.agent_credentials import AgentCredential
from app.models.hardware_metrics import HardwareMetric
from app.models.network_metrics import NetworkMetric
from app.models.installed_software import InstalledSoftware
from app.models.incidents import Incident
from app.models.maintenance_records import MaintenanceRecord
from app.models.alerts import Alert
from app.models.users import User
from app.schemas.computers import (
    ComputerCreate, ComputerUpdate, ComputerResponse,
    ComputerListResponse, AgentKeyResponse
)
from app.schemas.hardware import HardwareMetricResponse
from app.schemas.network import NetworkMetricResponse
from app.schemas.software import SoftwareItemResponse
from app.schemas.incidents import IncidentResponse
from app.schemas.maintenance import MaintenanceResponse
from app.schemas.alerts import AlertResponse
from app.utils.pagination import PaginationParams
from app.utils.helpers import log_audit

router = APIRouter(prefix="/computers", tags=["Computers"])


@router.get("/", response_model=ComputerListResponse)
async def list_computers(
    pagination: PaginationParams = Depends(),
    status_filter: str = Query(None, alias="status"),
    location_id: int = Query(None),
    search: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List computers with optional filtering."""
    query = select(Computer).where(Computer.is_active == True)  # noqa

    if status_filter:
        query = query.where(Computer.status == status_filter)
    if location_id:
        query = query.where(Computer.location_id == location_id)
    if search:
        query = query.where(
            or_(
                Computer.hostname.ilike(f"%{search}%"),
                Computer.ip_address.ilike(f"%{search}%"),
                Computer.department.ilike(f"%{search}%"),
            )
        )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(Computer.hostname).offset(pagination.skip).limit(pagination.limit)
    )
    computers = result.scalars().all()

    return ComputerListResponse(
        items=computers,
        total=total,
        page=pagination.page,
        pages=max(1, -(-total // pagination.limit)),
    )


@router.post("/", response_model=ComputerResponse, status_code=http_status.HTTP_201_CREATED)
async def create_computer(
    request: Request,
    computer_data: ComputerCreate,
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Register a new computer (admin only)."""
    existing = await db.execute(
        select(Computer).where(Computer.hostname == computer_data.hostname)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Hostname already registered")

    computer = Computer(**computer_data.model_dump())
    db.add(computer)
    await db.flush()

    await log_audit(
        db,
        action="create_computer",
        user_id=current_user.id,
        entity_type="computer",
        entity_id=computer.id,
        details={"hostname": computer.hostname},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(computer)
    return computer


@router.get("/{computer_id}", response_model=ComputerResponse)
async def get_computer(
    computer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a computer by ID."""
    result = await db.execute(
        select(Computer).where(Computer.id == computer_id)
    )
    computer = result.scalar_one_or_none()
    if not computer:
        raise HTTPException(status_code=404, detail="Computer not found")
    return computer


@router.put("/{computer_id}", response_model=ComputerResponse)
async def update_computer(
    computer_id: int,
    request: Request,
    update_data: ComputerUpdate,
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update a computer (admin only)."""
    result = await db.execute(select(Computer).where(Computer.id == computer_id))
    computer = result.scalar_one_or_none()
    if not computer:
        raise HTTPException(status_code=404, detail="Computer not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(computer, key, value)

    await log_audit(
        db,
        action="update_computer",
        user_id=current_user.id,
        entity_type="computer",
        entity_id=computer_id,
        details=update_dict,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(computer)
    return computer


@router.delete("/{computer_id}")
async def deactivate_computer(
    computer_id: int,
    request: Request,
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete (deactivate) a computer (admin only)."""
    result = await db.execute(select(Computer).where(Computer.id == computer_id))
    computer = result.scalar_one_or_none()
    if not computer:
        raise HTTPException(status_code=404, detail="Computer not found")

    computer.is_active = False
    await log_audit(
        db,
        action="deactivate_computer",
        user_id=current_user.id,
        entity_type="computer",
        entity_id=computer_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": "Computer deactivated"}


@router.get("/{computer_id}/hardware-metrics", response_model=list[HardwareMetricResponse])
async def get_hardware_metrics(
    computer_id: int,
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the last N hardware metrics for a computer."""
    result = await db.execute(
        select(HardwareMetric)
        .where(HardwareMetric.computer_id == computer_id)
        .order_by(HardwareMetric.recorded_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{computer_id}/network-metrics", response_model=list[NetworkMetricResponse])
async def get_network_metrics(
    computer_id: int,
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the last N network metrics for a computer."""
    result = await db.execute(
        select(NetworkMetric)
        .where(NetworkMetric.computer_id == computer_id)
        .order_by(NetworkMetric.recorded_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{computer_id}/software", response_model=list[SoftwareItemResponse])
async def get_computer_software(
    computer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get installed software for a computer."""
    result = await db.execute(
        select(InstalledSoftware)
        .where(InstalledSoftware.computer_id == computer_id, InstalledSoftware.is_active == True)  # noqa
        .order_by(InstalledSoftware.name)
    )
    return result.scalars().all()


@router.get("/{computer_id}/incidents", response_model=list[IncidentResponse])
async def get_computer_incidents(
    computer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get incidents for a computer."""
    result = await db.execute(
        select(Incident)
        .options(selectinload(Incident.updates))
        .where(Incident.computer_id == computer_id)
        .order_by(Incident.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.get("/{computer_id}/maintenance", response_model=list[MaintenanceResponse])
async def get_computer_maintenance(
    computer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get maintenance records for a computer."""
    result = await db.execute(
        select(MaintenanceRecord)
        .where(MaintenanceRecord.computer_id == computer_id)
        .order_by(MaintenanceRecord.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{computer_id}/alerts", response_model=list[AlertResponse])
async def get_computer_alerts(
    computer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get active alerts for a computer."""
    result = await db.execute(
        select(Alert)
        .where(Alert.computer_id == computer_id)
        .order_by(Alert.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.post("/{computer_id}/generate-agent-key", response_model=AgentKeyResponse)
async def generate_agent_key(
    computer_id: int,
    request: Request,
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new API key for the monitoring agent.
    The plaintext key is returned once — store it securely.
    """
    result = await db.execute(select(Computer).where(Computer.id == computer_id))
    computer = result.scalar_one_or_none()
    if not computer:
        raise HTTPException(status_code=404, detail="Computer not found")

    # Deactivate existing keys
    existing_keys = await db.execute(
        select(AgentCredential).where(
            AgentCredential.computer_id == computer_id,
            AgentCredential.is_active == True,  # noqa
        )
    )
    for cred in existing_keys.scalars().all():
        cred.is_active = False

    # Generate a new key
    plain_key = secrets.token_urlsafe(32)
    hashed_key = hash_password(plain_key)

    cred = AgentCredential(
        computer_id=computer_id,
        key_hash=hashed_key,
        label=f"Generated by {current_user.email}",
    )
    db.add(cred)

    await log_audit(
        db,
        action="generate_agent_key",
        user_id=current_user.id,
        entity_type="computer",
        entity_id=computer_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    return AgentKeyResponse(
        computer_id=computer_id,
        api_key=plain_key,
        message="Store this key securely. It will not be shown again.",
    )
