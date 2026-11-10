from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text, String, Enum as SAEnum, Index
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class UpdateType(str, enum.Enum):
    comment = "comment"
    status_change = "status_change"
    assignment = "assignment"
    resolution = "resolution"


class IncidentUpdate(Base):
    __tablename__ = "incident_updates"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    update_type = Column(SAEnum(UpdateType), default=UpdateType.comment, nullable=False)
    message = Column(Text, nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    incident = relationship("Incident", back_populates="updates")
    user = relationship("User")

    __table_args__ = (
        Index("ix_incident_updates_incident_id", "incident_id"),
        Index("ix_incident_updates_created_at", "created_at"),
    )
