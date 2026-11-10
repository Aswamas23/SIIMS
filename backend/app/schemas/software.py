from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date


class SoftwareItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    computer_id: int
    name: str
    version: Optional[str] = None
    publisher: Optional[str] = None
    install_date: Optional[date] = None
    first_seen: datetime
    last_seen: datetime
    is_active: bool


class SoftwareListResponse(BaseModel):
    items: list[SoftwareItemResponse]
    total: int
    page: int
    pages: int


class SoftwareSummaryItem(BaseModel):
    name: str
    count: int
    versions: list[str]
