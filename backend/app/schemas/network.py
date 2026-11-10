from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class NetworkMetricCreate(BaseModel):
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


class NetworkMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    computer_id: int
    recorded_at: datetime
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
