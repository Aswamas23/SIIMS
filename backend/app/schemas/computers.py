from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.computers import ComputerStatus


class ComputerCreate(BaseModel):
    hostname: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    processor: Optional[str] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    operating_system: Optional[str] = None
    os_version: Optional[str] = None
    location_id: Optional[int] = None
    department: Optional[str] = None
    notes: Optional[str] = None


class ComputerUpdate(BaseModel):
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    processor: Optional[str] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    operating_system: Optional[str] = None
    os_version: Optional[str] = None
    location_id: Optional[int] = None
    department: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ComputerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hostname: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    processor: Optional[str] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    operating_system: Optional[str] = None
    os_version: Optional[str] = None
    location_id: Optional[int] = None
    department: Optional[str] = None
    is_active: bool
    status: ComputerStatus
    notes: Optional[str] = None
    registered_at: datetime
    last_seen: Optional[datetime] = None
    updated_at: datetime


class ComputerListResponse(BaseModel):
    items: list[ComputerResponse]
    total: int
    page: int
    pages: int


class AgentKeyResponse(BaseModel):
    computer_id: int
    api_key: str
    message: str
