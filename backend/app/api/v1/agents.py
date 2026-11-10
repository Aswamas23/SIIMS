from datetime import datetime, timezone, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_agent
from app.models.computers import Computer, ComputerStatus
from app.models.hardware_metrics import HardwareMetric
from app.models.network_metrics import NetworkMetric
from app.models.installed_software import InstalledSoftware
from app.models.system_settings import SystemSetting
from app.schemas.agents import (
    HeartbeatPayload, SoftwareInventoryPayload,
    NetworkStatusPayload, AgentConfigResponse
)
from app.utils.helpers import get_setting

router = APIRouter(prefix="/agents", tags=["Agent"])


@router.post("/heartbeat")
async def heartbeat(
    payload: HeartbeatPayload,
    computer: Computer = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive a heartbeat from the monitoring agent.
    Records hardware and network metrics, updates computer last_seen.
    """
    now = datetime.now(timezone.utc)

    # Insert hardware metric
    hw = HardwareMetric(
        computer_id=computer.id,
        recorded_at=now,
        cpu_percent=payload.cpu_percent,
        cpu_freq_mhz=payload.cpu_freq_mhz,
        cpu_count_logical=payload.cpu_count_logical,
        cpu_temp_celsius=payload.cpu_temp_celsius,
        ram_total_gb=payload.ram_total_gb,
        ram_used_gb=payload.ram_used_gb,
        ram_percent=payload.ram_percent,
        disk_total_gb=payload.disk_total_gb,
        disk_used_gb=payload.disk_used_gb,
        disk_free_gb=payload.disk_free_gb,
        disk_percent=payload.disk_percent,
        smart_status=payload.smart_status,
        uptime_seconds=payload.uptime_seconds,
        battery_percent=payload.battery_percent,
        battery_plugged=payload.battery_plugged,
    )
    db.add(hw)

    # Insert network metric
    net = NetworkMetric(
        computer_id=computer.id,
        recorded_at=now,
        interface_name=payload.interface_name,
        ip_address=payload.ip_address,
        mac_address=payload.mac_address,
        is_up=payload.is_up,
        gateway_reachable=payload.gateway_reachable,
        dns_resolves=payload.dns_resolves,
        server_reachable=payload.server_reachable,
        latency_ms=payload.latency_ms,
        packet_loss_percent=payload.packet_loss_percent,
        bytes_sent=payload.bytes_sent,
        bytes_recv=payload.bytes_recv,
    )
    db.add(net)

    # Update computer last_seen and status
    computer.last_seen = now
    computer.status = ComputerStatus.online

    # Update IP if provided
    if payload.ip_address:
        computer.ip_address = payload.ip_address
    if payload.hostname:
        computer.hostname = payload.hostname
    if payload.os_version:
        computer.os_version = payload.os_version

    await db.commit()
    return {"status": "ok", "timestamp": now.isoformat()}


@router.post("/software-inventory")
async def update_software_inventory(
    payload: SoftwareInventoryPayload,
    computer: Computer = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Receive full software inventory from the agent. Upsert records."""
    now = datetime.now(timezone.utc)

    # Get current active software for this computer
    result = await db.execute(
        select(InstalledSoftware).where(
            InstalledSoftware.computer_id == computer.id,
            InstalledSoftware.is_active == True,  # noqa
        )
    )
    existing_software = {sw.name: sw for sw in result.scalars().all()}

    reported_names = set()
    for item in payload.software:
        if not item.name:
            continue
        reported_names.add(item.name)

        # Parse install date
        install_date = None
        if item.install_date and len(item.install_date) == 8:
            try:
                install_date = date(
                    int(item.install_date[:4]),
                    int(item.install_date[4:6]),
                    int(item.install_date[6:8]),
                )
            except (ValueError, TypeError):
                pass

        if item.name in existing_software:
            # Update existing
            sw = existing_software[item.name]
            sw.version = item.version
            sw.publisher = item.publisher
            sw.install_date = install_date
            sw.last_seen = now
        else:
            # Insert new
            sw = InstalledSoftware(
                computer_id=computer.id,
                name=item.name,
                version=item.version,
                publisher=item.publisher,
                install_date=install_date,
                first_seen=now,
                last_seen=now,
            )
            db.add(sw)

    # Mark software no longer present as inactive
    for name, sw in existing_software.items():
        if name not in reported_names:
            sw.is_active = False

    await db.commit()
    return {"status": "ok", "count": len(payload.software)}


@router.post("/network-status")
async def update_network_status(
    payload: NetworkStatusPayload,
    computer: Computer = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Record a network status update from the agent."""
    now = datetime.now(timezone.utc)

    net = NetworkMetric(
        computer_id=computer.id,
        recorded_at=now,
        interface_name=payload.interface_name,
        ip_address=payload.ip_address,
        mac_address=payload.mac_address,
        is_up=payload.is_up,
        gateway_reachable=payload.gateway_reachable,
        dns_resolves=payload.dns_resolves,
        server_reachable=payload.server_reachable,
        latency_ms=payload.latency_ms,
        packet_loss_percent=payload.packet_loss_percent,
        bytes_sent=payload.bytes_sent,
        bytes_recv=payload.bytes_recv,
    )
    db.add(net)
    await db.commit()
    return {"status": "ok"}


@router.get("/config", response_model=AgentConfigResponse)
async def get_agent_config(
    computer: Computer = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Return configuration for the monitoring agent."""
    return AgentConfigResponse(
        heartbeat_interval_seconds=await get_setting(db, "heartbeat_interval_seconds", 60),
        software_scan_interval_hours=await get_setting(db, "software_scan_interval_hours", 24),
        data_retention_days=await get_setting(db, "data_retention_days", 30),
    )
