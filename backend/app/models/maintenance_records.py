from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Date, Enum as SAEnum, Index
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class MaintenanceType(str, enum.Enum):
    preventive = "preventive"
    corrective = "corrective"
    upgrade = "upgrade"
    inspection = "inspection"
    other = "other"


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, index=True)
    computer_id = Column(Integer, ForeignKey("computers.id", ondelete="CASCADE"), nullable=False, index=True)
    performed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    maintenance_type = Column(SAEnum(MaintenanceType), default=MaintenanceType.preventive, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    cost = Column(Integer, nullable=True)  # In cents
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    computer = relationship("Computer", back_populates="maintenance_records")
    performed_by = relationship("User")

    __table_args__ = (
        Index("ix_maintenance_records_computer_id", "computer_id"),
        Index("ix_maintenance_records_scheduled_date", "scheduled_date"),
        Index("ix_maintenance_records_completed_date", "completed_date"),
    )
