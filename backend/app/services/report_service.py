import io
import csv
from datetime import date, datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)


async def generate_report(
    db: AsyncSession,
    report_type: str,
    format: str = "pdf",
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    location_id: Optional[int] = None,
    computer_id: Optional[int] = None,
) -> tuple[bytes, str]:
    """
    Generate a report. Returns (bytes, content_type).
    Dispatches to per-type functions.
    """
    generators = {
        "computers": _generate_computers_report,
        "hardware": _generate_hardware_report,
        "network": _generate_network_report,
        "software": _generate_software_report,
        "licences": _generate_licences_report,
        "incidents": _generate_incidents_report,
        "maintenance": _generate_maintenance_report,
        "downtime": _generate_downtime_report,
    }

    generator = generators.get(report_type)
    if not generator:
        raise ValueError(f"Unknown report type: {report_type}")

    data = await generator(db, date_from=date_from, date_to=date_to,
                           location_id=location_id, computer_id=computer_id)

    if format == "pdf":
        return await _to_pdf(data, report_type), "application/pdf"
    elif format == "excel":
        return await _to_excel(data, report_type), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif format == "csv":
        return await _to_csv(data), "text/csv"
    else:
        raise ValueError(f"Unknown format: {format}")


async def _generate_computers_report(db, **kwargs):
    from app.models.computers import Computer
    result = await db.execute(
        select(Computer).where(Computer.is_active == True).order_by(Computer.hostname)  # noqa
    )
    computers = result.scalars().all()
    return {
        "title": "Computer Asset Report",
        "headers": ["ID", "Hostname", "IP Address", "Status", "Location", "OS", "Last Seen"],
        "rows": [
            [c.id, c.hostname, c.ip_address or "", c.status, c.location_id or "", c.operating_system or "", str(c.last_seen or "")]
            for c in computers
        ],
    }


async def _generate_hardware_report(db, **kwargs):
    from app.models.hardware_metrics import HardwareMetric
    from app.models.computers import Computer
    from sqlalchemy import func

    # Latest metric per computer
    subq = (
        select(
            HardwareMetric.computer_id,
            func.max(HardwareMetric.recorded_at).label("max_ts"),
        )
        .group_by(HardwareMetric.computer_id)
        .subquery()
    )
    result = await db.execute(
        select(HardwareMetric, Computer.hostname)
        .join(subq, (HardwareMetric.computer_id == subq.c.computer_id) & (HardwareMetric.recorded_at == subq.c.max_ts))
        .join(Computer, Computer.id == HardwareMetric.computer_id)
    )
    rows = result.all()
    return {
        "title": "Hardware Metrics Report",
        "headers": ["Computer", "CPU%", "RAM%", "Disk%", "Recorded At"],
        "rows": [
            [hostname, m.cpu_percent, m.ram_percent, m.disk_percent, str(m.recorded_at)]
            for m, hostname in rows
        ],
    }


async def _generate_network_report(db, **kwargs):
    from app.models.network_metrics import NetworkMetric
    from app.models.computers import Computer
    from sqlalchemy import func

    subq = (
        select(
            NetworkMetric.computer_id,
            func.max(NetworkMetric.recorded_at).label("max_ts"),
        )
        .group_by(NetworkMetric.computer_id)
        .subquery()
    )
    result = await db.execute(
        select(NetworkMetric, Computer.hostname)
        .join(subq, (NetworkMetric.computer_id == subq.c.computer_id) & (NetworkMetric.recorded_at == subq.c.max_ts))
        .join(Computer, Computer.id == NetworkMetric.computer_id)
    )
    rows = result.all()
    return {
        "title": "Network Status Report",
        "headers": ["Computer", "IP", "Latency ms", "Packet Loss%", "Gateway OK", "Recorded At"],
        "rows": [
            [hostname, m.ip_address, m.latency_ms, m.packet_loss_percent, m.gateway_reachable, str(m.recorded_at)]
            for m, hostname in rows
        ],
    }


async def _generate_software_report(db, **kwargs):
    from app.models.installed_software import InstalledSoftware
    from app.models.computers import Computer

    result = await db.execute(
        select(InstalledSoftware, Computer.hostname)
        .join(Computer, Computer.id == InstalledSoftware.computer_id)
        .where(InstalledSoftware.is_active == True)  # noqa
        .order_by(Computer.hostname, InstalledSoftware.name)
    )
    rows = result.all()
    return {
        "title": "Software Inventory Report",
        "headers": ["Computer", "Software", "Version", "Publisher"],
        "rows": [
            [hostname, s.name, s.version or "", s.publisher or ""]
            for s, hostname in rows
        ],
    }


async def _generate_licences_report(db, **kwargs):
    from app.models.software_licences import SoftwareLicence

    result = await db.execute(
        select(SoftwareLicence).order_by(SoftwareLicence.expiry_date)
    )
    licences = result.scalars().all()
    return {
        "title": "Software Licences Report",
        "headers": ["Software", "Vendor", "Seats", "Expiry Date", "Status"],
        "rows": [
            [l.software_name, l.vendor or "", l.seats or "", str(l.expiry_date or ""), l.status]
            for l in licences
        ],
    }


async def _generate_incidents_report(db, date_from=None, date_to=None, **kwargs):
    from app.models.incidents import Incident

    query = select(Incident).order_by(Incident.created_at.desc())
    if date_from:
        query = query.where(Incident.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.where(Incident.created_at <= datetime.combine(date_to, datetime.max.time()))

    result = await db.execute(query)
    incidents = result.scalars().all()
    return {
        "title": "Incidents Report",
        "headers": ["Incident #", "Title", "Severity", "Status", "Category", "Created At", "Resolved At"],
        "rows": [
            [i.incident_number, i.title, i.severity, i.status, i.category, str(i.created_at), str(i.resolved_at or "")]
            for i in incidents
        ],
    }


async def _generate_maintenance_report(db, **kwargs):
    from app.models.maintenance_records import MaintenanceRecord
    from app.models.computers import Computer

    result = await db.execute(
        select(MaintenanceRecord, Computer.hostname)
        .join(Computer, Computer.id == MaintenanceRecord.computer_id)
        .order_by(MaintenanceRecord.created_at.desc())
    )
    rows = result.all()
    return {
        "title": "Maintenance Report",
        "headers": ["Computer", "Type", "Title", "Scheduled", "Completed"],
        "rows": [
            [hostname, m.maintenance_type, m.title, str(m.scheduled_date or ""), str(m.completed_date or "")]
            for m, hostname in rows
        ],
    }


async def _generate_downtime_report(db, **kwargs):
    from app.models.alerts import Alert, AlertType

    result = await db.execute(
        select(Alert).where(Alert.alert_type == AlertType.computer_offline)
        .order_by(Alert.created_at.desc())
    )
    alerts = result.scalars().all()
    return {
        "title": "Downtime Report",
        "headers": ["Computer ID", "Alert Created", "Alert Resolved", "Duration"],
        "rows": [
            [
                a.computer_id,
                str(a.created_at),
                str(a.resolved_at or "Ongoing"),
                str((a.resolved_at - a.created_at) if a.resolved_at else "Ongoing"),
            ]
            for a in alerts
        ],
    }


async def _to_pdf(data: dict, report_type: str) -> bytes:
    """Generate a PDF report using ReportLab platypus."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(data["title"], styles["Title"]))
    story.append(Spacer(1, 20))

    # Table
    table_data = [data["headers"]] + data["rows"]
    if len(table_data) > 1:
        t = Table(table_data, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No data available", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()


async def _to_excel(data: dict, report_type: str) -> bytes:
    """Generate an Excel report using openpyxl."""
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font

    wb = Workbook()
    ws = wb.active
    ws.title = data["title"][:31]  # Excel sheet name limit

    # Header row
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    for col_idx, header in enumerate(data["headers"], start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font

    # Data rows
    for row_idx, row in enumerate(data["rows"], start=2):
        for col_idx, value in enumerate(row, start=1):
            ws.cell(row=row_idx, column=col_idx, value=str(value) if value is not None else "")

    # Auto-size columns
    for col in ws.columns:
        max_length = max((len(str(cell.value)) for cell in col if cell.value), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 50)

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


async def _to_csv(data: dict) -> bytes:
    """Generate a CSV report."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(data["headers"])
    for row in data["rows"]:
        writer.writerow([str(v) if v is not None else "" for v in row])
    return buffer.getvalue().encode("utf-8")
