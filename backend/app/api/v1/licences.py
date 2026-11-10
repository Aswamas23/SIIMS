from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.software_licences import SoftwareLicence
from app.models.licence_assignments import LicenceAssignment
from app.models.users import User
from app.schemas.licences import (
    LicenceCreate, LicenceUpdate, LicenceResponse, LicenceAssignRequest
)
from app.utils.pagination import PaginationParams
from app.utils.helpers import log_audit

router = APIRouter(prefix="/licences", tags=["Licences"])


async def _build_licence_response(licence: SoftwareLicence, db: AsyncSession) -> LicenceResponse:
    count_result = await db.execute(
        select(func.count(LicenceAssignment.id)).where(
            LicenceAssignment.licence_id == licence.id
        )
    )
    count = count_result.scalar_one()
    response = LicenceResponse.model_validate(licence)
    response.assignments_count = count
    return response


@router.get("/", response_model=list[LicenceResponse])
async def list_licences(
    pagination: PaginationParams = Depends(),
    is_active: bool = Query(True),
    search: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List software licences."""
    query = select(SoftwareLicence).where(SoftwareLicence.is_active == is_active)
    if search:
        query = query.where(SoftwareLicence.software_name.ilike(f"%{search}%"))

    result = await db.execute(
        query.order_by(SoftwareLicence.software_name)
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    licences = result.scalars().all()
    return [await _build_licence_response(lic, db) for lic in licences]


@router.post("/", response_model=LicenceResponse, status_code=status.HTTP_201_CREATED)
async def create_licence(
    request: Request,
    licence_data: LicenceCreate,
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new software licence (admin only)."""
    licence = SoftwareLicence(**licence_data.model_dump())
    db.add(licence)
    await db.flush()

    await log_audit(
        db,
        action="create_licence",
        user_id=current_user.id,
        entity_type="licence",
        entity_id=licence.id,
        details={"software_name": licence.software_name},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(licence)
    return await _build_licence_response(licence, db)


@router.get("/expiring", response_model=list[LicenceResponse])
async def get_expiring_licences(
    days: int = Query(30, description="Licences expiring within this many days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get licences expiring within N days."""
    today = date.today()
    cutoff = today + timedelta(days=days)
    result = await db.execute(
        select(SoftwareLicence).where(
            SoftwareLicence.expiry_date.isnot(None),
            SoftwareLicence.expiry_date <= cutoff,
            SoftwareLicence.is_active == True,  # noqa
        ).order_by(SoftwareLicence.expiry_date)
    )
    licences = result.scalars().all()
    return [await _build_licence_response(lic, db) for lic in licences]


@router.get("/{licence_id}", response_model=LicenceResponse)
async def get_licence(
    licence_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a licence by ID."""
    result = await db.execute(select(SoftwareLicence).where(SoftwareLicence.id == licence_id))
    licence = result.scalar_one_or_none()
    if not licence:
        raise HTTPException(status_code=404, detail="Licence not found")
    return await _build_licence_response(licence, db)


@router.put("/{licence_id}", response_model=LicenceResponse)
async def update_licence(
    licence_id: int,
    request: Request,
    update_data: LicenceUpdate,
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update a licence (admin only)."""
    result = await db.execute(select(SoftwareLicence).where(SoftwareLicence.id == licence_id))
    licence = result.scalar_one_or_none()
    if not licence:
        raise HTTPException(status_code=404, detail="Licence not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(licence, key, value)

    await log_audit(
        db,
        action="update_licence",
        user_id=current_user.id,
        entity_type="licence",
        entity_id=licence_id,
        details=update_dict,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(licence)
    return await _build_licence_response(licence, db)


@router.delete("/{licence_id}")
async def delete_licence(
    licence_id: int,
    request: Request,
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a licence (admin only)."""
    result = await db.execute(select(SoftwareLicence).where(SoftwareLicence.id == licence_id))
    licence = result.scalar_one_or_none()
    if not licence:
        raise HTTPException(status_code=404, detail="Licence not found")

    licence.is_active = False
    await log_audit(
        db,
        action="delete_licence",
        user_id=current_user.id,
        entity_type="licence",
        entity_id=licence_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": "Licence deactivated"}


@router.post("/{licence_id}/assign")
async def assign_licence(
    licence_id: int,
    request: Request,
    assign_data: LicenceAssignRequest,
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Assign a licence to a computer (admin only)."""
    # Check licence exists
    result = await db.execute(select(SoftwareLicence).where(SoftwareLicence.id == licence_id))
    licence = result.scalar_one_or_none()
    if not licence:
        raise HTTPException(status_code=404, detail="Licence not found")

    # Check not already assigned
    existing = await db.execute(
        select(LicenceAssignment).where(
            LicenceAssignment.licence_id == licence_id,
            LicenceAssignment.computer_id == assign_data.computer_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Licence already assigned to this computer")

    assignment = LicenceAssignment(
        licence_id=licence_id,
        computer_id=assign_data.computer_id,
    )
    db.add(assignment)

    await log_audit(
        db,
        action="assign_licence",
        user_id=current_user.id,
        entity_type="licence",
        entity_id=licence_id,
        details={"computer_id": assign_data.computer_id},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": "Licence assigned"}


@router.delete("/{licence_id}/assign/{computer_id}")
async def remove_licence_assignment(
    licence_id: int,
    computer_id: int,
    request: Request,
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Remove a licence assignment from a computer (admin only)."""
    result = await db.execute(
        select(LicenceAssignment).where(
            LicenceAssignment.licence_id == licence_id,
            LicenceAssignment.computer_id == computer_id,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    await db.delete(assignment)
    await log_audit(
        db,
        action="remove_licence_assignment",
        user_id=current_user.id,
        entity_type="licence",
        entity_id=licence_id,
        details={"computer_id": computer_id},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": "Assignment removed"}
