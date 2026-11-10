from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class HeartbeatPayload(BaseModel):
    """Payload sent by the monitoring agent on each heartbeat."""
    # Hardware metrics
    cpu_percent: Optional[float] = None
    cpu_freq_mhz: Optional[float] = None
    cpu_count_logical: Optional[int] = None
    cpu_temp_celsius: Optional[float] = None
    ram_total_gb: Optional[float] = None
    ram_used_gb: Optional[float] = None
    ram_percent: Optional[float] = None
    disk_total_gb: Optional[float] = None
    disk_used_gb: Optional[float] = None
    disk_free_gb: Optional[float] = None
    disk_percent: Optional[float] = None
    smart_status: Optional[str] = None
    uptime_seconds: Optional[int] = None
    battery_percent: Optional[float] = None
    battery_plugged: Optional[bool] = None

    # Network metrics
    interface_name: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    is_up: Optional[bool] = None
    gateway_reachable: Optional[bool] = None
    dns_resolves: Optional[bool] = None
    server_reachable: Optional[bool] = None
    latency_ms: Optional[float] = None
    packet_loss_percent: Optional[float] = None
    bytes_sent: Optional[int] = None
    bytes_recv: Optional[int] = None

    # System info updates
    hostname: Optional[str] = None
    os_version: Optional[str] = None


class SoftwareInventoryItem(BaseModel):
    name: str
    version: Optional[str] = None
    publisher: Optional[str] = None
    install_date: Optional[str] = None  # String from registry, e.g. "20231015"


class SoftwareInventoryPayload(BaseModel):
    software: list[SoftwareInventoryItem]


class NetworkStatusPayload(BaseModel):
    interface_name: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    is_up: Optional[bool] = None
    gateway_reachable: Optional[bool] = None
    dns_resolves: Optional[bool] = None
    server_reachable: Optional[bool] = None
    latency_ms: Optional[float] = None
    packet_loss_percent: Optional[float] = None
    bytes_sent: Optional[int] = None
    bytes_recv: Optional[int] = None


class AgentConfigResponse(BaseModel):
    heartbeat_interval_seconds: int
    software_scan_interval_hours: int
    data_retention_days: int
