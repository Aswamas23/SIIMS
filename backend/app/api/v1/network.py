from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.network_metrics import NetworkMetric
from app.models.users import User
from app.schemas.network import NetworkMetricResponse
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/network", tags=["Network"])


@router.get("/status", response_model=list[NetworkMetricResponse])
async def get_network_status(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest network metric per computer."""
    subq = (
        select(
            NetworkMetric.computer_id,
            func.max(NetworkMetric.recorded_at).label("max_recorded_at"),
        )
        .group_by(NetworkMetric.computer_id)
        .subquery()
    )

    result = await db.execute(
        select(NetworkMetric)
        .join(
            subq,
            (NetworkMetric.computer_id == subq.c.computer_id)
            & (NetworkMetric.recorded_at == subq.c.max_recorded_at),
        )
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    return result.scalars().all()


@router.get("/metrics", response_model=list[NetworkMetricResponse])
async def get_network_metrics_timeseries(
    computer_id: int = Query(..., description="Computer ID is required"),
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get time-series network metrics for a specific computer."""
    result = await db.execute(
        select(NetworkMetric)
        .where(NetworkMetric.computer_id == computer_id)
        .order_by(NetworkMetric.recorded_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
