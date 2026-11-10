from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.locations import Location
from app.models.users import User
from app.schemas.locations import LocationCreate, LocationUpdate, LocationResponse
from app.utils.helpers import log_audit

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("/", response_model=list[LocationResponse])
async def list_locations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all locations."""
    result = await db.execute(select(Location).order_by(Location.name))
    return result.scalars().all()


@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    request: Request,
    location_data: LocationCreate,
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new location (admin only)."""
    existing = await db.execute(
        select(Location).where(Location.name == location_data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Location name already exists")

    location = Location(**location_data.model_dump())
    db.add(location)
    await db.flush()

    await log_audit(
        db,
        action="create_location",
        user_id=current_user.id,
        entity_type="location",
        entity_id=location.id,
        details={"name": location.name},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(location)
    return location


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: int,
    request: Request,
    update_data: LocationUpdate,
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update a location (admin only)."""
    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(location, key, value)

    await log_audit(
        db,
        action="update_location",
        user_id=current_user.id,
        entity_type="location",
        entity_id=location_id,
        details=update_dict,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(location)
    return location


@router.delete("/{location_id}")
async def delete_location(
    location_id: int,
    request: Request,
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a location (admin only). Computers in this location will have NULL location."""
    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    await db.delete(location)
    await log_audit(
        db,
        action="delete_location",
        user_id=current_user.id,
        entity_type="location",
        entity_id=location_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": "Location deleted"}
