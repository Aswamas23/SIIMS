from typing import Callable, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError

from app.core.database import get_db
from app.core.security import decode_token, verify_password

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Decode Bearer JWT and return the authenticated User model."""
    # Import here to avoid circular imports
    from app.models.users import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        select(User).where(User.id == int(user_id), User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


def require_role(*roles: str) -> Callable:
    """Return a dependency that raises 403 if user role is not in the allowed set."""

    async def role_guard(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(roles)}",
            )
        return current_user

    return role_guard


async def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate an agent using Bearer <api_key> against bcrypt hash in agent_credentials."""
    from app.models.agent_credentials import AgentCredential
    from app.models.computers import Computer

    auth_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid agent credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    plain_key = credentials.credentials

    # Retrieve all active credentials and verify bcrypt (no index on hash, must scan)
    result = await db.execute(
        select(AgentCredential).where(AgentCredential.is_active == True)  # noqa: E712
    )
    agent_creds = result.scalars().all()

    matched_cred = None
    for cred in agent_creds:
        if verify_password(plain_key, cred.key_hash):
            matched_cred = cred
            break

    if matched_cred is None:
        raise auth_exception

    # Return the associated computer
    computer_result = await db.execute(
        select(Computer).where(Computer.id == matched_cred.computer_id)
    )
    computer = computer_result.scalar_one_or_none()
    if computer is None:
        raise auth_exception

    return computer
