from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.users import User
from app.services.report_service import generate_report

router = APIRouter(prefix="/reports", tags=["Reports"])

REPORT_EXTENSIONS = {
    "pdf": "pdf",
    "excel": "xlsx",
    "csv": "csv",
}


def _build_response(data: bytes, content_type: str, report_type: str, fmt: str) -> Response:
    ext = REPORT_EXTENSIONS.get(fmt, "bin")
    filename = f"siims_{report_type}_report.{ext}"
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/computers")
async def report_computers(
    format: str = Query("pdf", pattern="^(pdf|excel|csv)$"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    location_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data, content_type = await generate_report(db, "computers", format, date_from, date_to, location_id)
    return _build_response(data, content_type, "computers", format)


@router.get("/hardware")
async def report_hardware(
    format: str = Query("pdf", pattern="^(pdf|excel|csv)$"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    location_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data, content_type = await generate_report(db, "hardware", format, date_from, date_to, location_id)
    return _build_response(data, content_type, "hardware", format)


@router.get("/network")
async def report_network(
    format: str = Query("pdf", pattern="^(pdf|excel|csv)$"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data, content_type = await generate_report(db, "network", format, date_from, date_to)
    return _build_response(data, content_type, "network", format)


@router.get("/software")
async def report_software(
    format: str = Query("pdf", pattern="^(pdf|excel|csv)$"),
    computer_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data, content_type = await generate_report(db, "software", format, computer_id=computer_id)
    return _build_response(data, content_type, "software", format)


@router.get("/licences")
async def report_licences(
    format: str = Query("pdf", pattern="^(pdf|excel|csv)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data, content_type = await generate_report(db, "licences", format)
    return _build_response(data, content_type, "licences", format)


@router.get("/incidents")
async def report_incidents(
    format: str = Query("pdf", pattern="^(pdf|excel|csv)$"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data, content_type = await generate_report(db, "incidents", format, date_from, date_to)
    return _build_response(data, content_type, "incidents", format)


@router.get("/maintenance")
async def report_maintenance(
    format: str = Query("pdf", pattern="^(pdf|excel|csv)$"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data, content_type = await generate_report(db, "maintenance", format, date_from, date_to)
    return _build_response(data, content_type, "maintenance", format)


@router.get("/downtime")
async def report_downtime(
    format: str = Query("pdf", pattern="^(pdf|excel|csv)$"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data, content_type = await generate_report(db, "downtime", format, date_from, date_to)
    return _build_response(data, content_type, "downtime", format)
