from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token, decode_token
)
from app.core.dependencies import get_current_user
from app.models.users import User
from app.models.users import RefreshToken
from app.schemas.auth import (
    LoginRequest, TokenResponse, RefreshRequest,
    AccessTokenResponse, ChangePasswordRequest, LogoutRequest
)
from app.schemas.users import UserResponse, UserUpdate
from app.utils.helpers import log_audit
from app.core.config import settings
from app.core.limiter import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user credentials and return access + refresh tokens."""
    result = await db.execute(
        select(User).where(User.email == login_data.email.lower(), User.is_active == True)  # noqa
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create tokens
    access_token = create_access_token(str(user.id))
    refresh_token, jti = create_refresh_token(str(user.id))

    # Store refresh token
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = RefreshToken(
        user_id=user.id,
        jti=jti,
        expires_at=expires_at,
    )
    db.add(db_token)

    # Update last login
    user.last_login = datetime.now(timezone.utc)

    await log_audit(
        db,
        action="login",
        user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_access_token(
    refresh_data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Issue a new access token using a valid refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )

    try:
        payload = decode_token(refresh_data.refresh_token)
        if payload.get("type") != "refresh":
            raise credentials_exception
        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    # Verify token not revoked
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.jti == jti,
            RefreshToken.is_revoked == False,  # noqa
        )
    )
    db_token = result.scalar_one_or_none()
    if db_token is None:
        raise credentials_exception

    # Check token expiry
    expires_at = db_token.expires_at
    if expires_at.tzinfo is None:
        from datetime import timezone as tz
        expires_at = expires_at.replace(tzinfo=tz.utc)
    if expires_at < datetime.now(timezone.utc):
        raise credentials_exception

    access_token = create_access_token(str(user_id))
    return AccessTokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(
    request: Request,
    logout_data: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke the refresh token to invalidate the session."""
    if logout_data.refresh_token:
        try:
            payload = decode_token(logout_data.refresh_token)
            jti = payload.get("jti")
            if jti:
                result = await db.execute(
                    select(RefreshToken).where(RefreshToken.jti == jti)
                )
                db_token = result.scalar_one_or_none()
                if db_token:
                    db_token.is_revoked = True
                    await db.commit()
        except Exception:
            pass  # Token already invalid, that's fine

    await log_audit(
        db,
        action="logout",
        user_id=current_user.id,
        entity_type="user",
        entity_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    request: Request,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's own profile (non-sensitive fields)."""
    update_dict = update_data.model_dump(exclude_unset=True, exclude={"role", "is_active"})
    for key, value in update_dict.items():
        setattr(current_user, key, value)

    await log_audit(
        db,
        action="update_profile",
        user_id=current_user.id,
        entity_type="user",
        entity_id=current_user.id,
        details=update_dict,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/me/change-password")
async def change_password(
    request: Request,
    change_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password."""
    if not verify_password(change_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(change_data.new_password)

    await log_audit(
        db,
        action="change_password",
        user_id=current_user.id,
        entity_type="user",
        entity_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": "Password changed successfully"}
