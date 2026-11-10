from pydantic import BaseModel
from typing import Optional
from datetime import date


class ReportRequest(BaseModel):
    format: str = "pdf"  # 'pdf', 'excel', 'csv'
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    location_id: Optional[int] = None
    computer_id: Optional[int] = None
