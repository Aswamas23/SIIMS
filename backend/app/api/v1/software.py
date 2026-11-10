from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.installed_software import InstalledSoftware
from app.models.users import User
from app.schemas.software import SoftwareItemResponse, SoftwareListResponse, SoftwareSummaryItem
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/software", tags=["Software"])


@router.get("/", response_model=SoftwareListResponse)
async def list_software(
    pagination: PaginationParams = Depends(),
    computer_id: int = Query(None),
    name: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List installed software across all computers, with optional filters."""
    query = select(InstalledSoftware).where(InstalledSoftware.is_active == True)  # noqa

    if computer_id:
        query = query.where(InstalledSoftware.computer_id == computer_id)
    if name:
        query = query.where(InstalledSoftware.name.ilike(f"%{name}%"))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(InstalledSoftware.name)
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    items = result.scalars().all()

    return SoftwareListResponse(
        items=items,
        total=total,
        page=pagination.page,
        pages=max(1, -(-total // pagination.limit)),
    )


@router.get("/summary", response_model=list[SoftwareSummaryItem])
async def get_software_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a count of each unique software name across all computers."""
    result = await db.execute(
        select(
            InstalledSoftware.name,
            func.count(InstalledSoftware.id).label("count"),
        )
        .where(InstalledSoftware.is_active == True)  # noqa
        .group_by(InstalledSoftware.name)
        .order_by(func.count(InstalledSoftware.id).desc())
        .limit(200)
    )
    rows = result.all()

    # For each software name, collect distinct versions (separate query or in-memory)
    summary = []
    for row in rows:
        versions_result = await db.execute(
            select(InstalledSoftware.version)
            .where(
                InstalledSoftware.name == row.name,
                InstalledSoftware.is_active == True,  # noqa
                InstalledSoftware.version.isnot(None),
            )
            .distinct()
            .limit(10)
        )
        versions = [v for (v,) in versions_result.all() if v]
        summary.append(
            SoftwareSummaryItem(name=row.name, count=row.count, versions=versions)
        )
    return summary


@router.get("/missing-required", response_model=list)
async def get_missing_required_software(
    current_user: User = Depends(get_current_user),
):
    """Placeholder: returns computers missing required software."""
    # Future implementation: compare installed software against a required list
    return []
