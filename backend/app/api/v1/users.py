import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.dependencies import require_role
from app.core.security import hash_password
from app.models.users import User
from app.schemas.users import (
    UserCreate, UserUpdate, UserResponse, UserListResponse, ResetPasswordResponse
)
from app.utils.pagination import PaginationParams
from app.utils.helpers import log_audit

router = APIRouter(prefix="/users", tags=["Users"])

ADMIN_ONLY = Depends(require_role("system_admin"))


@router.get("/", response_model=UserListResponse)
async def list_users(
    pagination: PaginationParams = Depends(),
    current_user: User = ADMIN_ONLY,
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar_one()

    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(pagination.skip).limit(pagination.limit)
    )
    users = result.scalars().all()

    return UserListResponse(
        items=users,
        total=total,
        page=pagination.page,
        pages=max(1, -(-total // pagination.limit)),
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    user_data: UserCreate,
    current_user: User = ADMIN_ONLY,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user (admin only)."""
    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == user_data.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_data.email.lower(),
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        phone=user_data.phone,
    )
    db.add(new_user)
    await db.flush()  # Get ID without committing

    await log_audit(
        db,
        action="create_user",
        user_id=current_user.id,
        entity_type="user",
        entity_id=new_user.id,
        details={"email": new_user.email, "role": new_user.role},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = ADMIN_ONLY,
    db: AsyncSession = Depends(get_db),
):
    """Get a user by ID (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: Request,
    update_data: UserUpdate,
    current_user: User = ADMIN_ONLY,
    db: AsyncSession = Depends(get_db),
):
    """Update a user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(user, key, value)

    await log_audit(
        db,
        action="update_user",
        user_id=current_user.id,
        entity_type="user",
        entity_id=user_id,
        details=update_dict,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: int,
    request: Request,
    current_user: User = ADMIN_ONLY,
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete (deactivate) a user (admin only)."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False

    await log_audit(
        db,
        action="deactivate_user",
        user_id=current_user.id,
        entity_type="user",
        entity_id=user_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": "User deactivated"}


@router.post("/{user_id}/reset-password", response_model=ResetPasswordResponse)
async def reset_user_password(
    user_id: int,
    request: Request,
    current_user: User = ADMIN_ONLY,
    db: AsyncSession = Depends(get_db),
):
    """Generate a temporary password for a user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate a random temporary password
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    temp_password = "".join(secrets.choice(alphabet) for _ in range(12))

    user.hashed_password = hash_password(temp_password)

    await log_audit(
        db,
        action="reset_password",
        user_id=current_user.id,
        entity_type="user",
        entity_id=user_id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    return ResetPasswordResponse(
        temp_password=temp_password,
        message="Temporary password generated. User must change it on next login.",
    )
