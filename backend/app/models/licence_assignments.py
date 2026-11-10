from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class LicenceAssignment(Base):
    __tablename__ = "licence_assignments"

    id = Column(Integer, primary_key=True, index=True)
    licence_id = Column(Integer, ForeignKey("software_licences.id", ondelete="CASCADE"), nullable=False, index=True)
    computer_id = Column(Integer, ForeignKey("computers.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    licence = relationship("SoftwareLicence", back_populates="assignments")
    computer = relationship("Computer", back_populates="licence_assignments")

    __table_args__ = (
        Index("ix_licence_assignments_licence_id", "licence_id"),
        Index("ix_licence_assignments_computer_id", "computer_id"),
    )
