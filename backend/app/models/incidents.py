from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SAEnum, Index
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class IncidentSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IncidentStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class IncidentCategory(str, enum.Enum):
    hardware = "hardware"
    software = "software"
    network = "network"
    security = "security"
    performance = "performance"
    maintenance = "maintenance"
    other = "other"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_number = Column(String(30), unique=True, nullable=False, index=True)
    computer_id = Column(Integer, ForeignKey("computers.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SAEnum(IncidentCategory), default=IncidentCategory.other, nullable=False, index=True)
    severity = Column(SAEnum(IncidentSeverity), default=IncidentSeverity.medium, nullable=False, index=True)
    status = Column(SAEnum(IncidentStatus), default=IncidentStatus.open, nullable=False, index=True)

    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Auto-created from alert
    is_auto_created = Column(Boolean, default=False, nullable=False)
    related_alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Relationships
    computer = relationship("Computer", back_populates="incidents")
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="created_incidents")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_incidents")
    updates = relationship("IncidentUpdate", back_populates="incident", cascade="all, delete-orphan")
    related_alert = relationship("Alert", foreign_keys=[related_alert_id])

    __table_args__ = (
        Index("ix_incidents_computer_id", "computer_id"),
        Index("ix_incidents_status", "status"),
        Index("ix_incidents_severity", "severity"),
        Index("ix_incidents_created_at", "created_at"),
        Index("ix_incidents_assigned_to_id", "assigned_to_id"),
    )
