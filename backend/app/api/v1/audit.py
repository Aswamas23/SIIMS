from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.audit_logs import AuditLog
from app.models.users import User
from app.schemas.audit import AuditLogResponse, AuditLogListResponse
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/", response_model=AuditLogListResponse)
async def list_audit_logs(
    pagination: PaginationParams = Depends(),
    user_id: int = Query(None),
    entity_type: str = Query(None),
    action: str = Query(None),
    date_from: datetime = Query(None),
    date_to: datetime = Query(None),
    current_user: User = Depends(require_role("system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """List audit logs (admin only)."""
    query = select(AuditLog)

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if action:
        query = query.where(AuditLog.action == action)
    if date_from:
        query = query.where(AuditLog.created_at >= date_from)
    if date_to:
        query = query.where(AuditLog.created_at <= date_to)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(AuditLog.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    items = result.scalars().all()

    return AuditLogListResponse(
        items=items,
        total=total,
        page=pagination.page,
        pages=max(1, -(-total // pagination.limit)),
    )
