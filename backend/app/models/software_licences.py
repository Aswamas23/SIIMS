from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, Index, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class LicenceStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    expiring_soon = "expiring_soon"
    perpetual = "perpetual"
    unknown = "unknown"


class SoftwareLicence(Base):
    __tablename__ = "software_licences"

    id = Column(Integer, primary_key=True, index=True)
    software_name = Column(String(500), nullable=False, index=True)
    version = Column(String(255), nullable=True)
    licence_key = Column(Text, nullable=True)  # Encrypted at rest recommended
    licence_type = Column(String(100), nullable=True)  # e.g., "per_seat", "site", "subscription"
    vendor = Column(String(500), nullable=True)
    seats = Column(Integer, nullable=True)  # Total allowed seats
    purchase_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True, index=True)
    cost = Column(Integer, nullable=True)  # In cents to avoid float precision
    notes = Column(Text, nullable=True)
    status = Column(SAEnum(LicenceStatus), default=LicenceStatus.active, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    assignments = relationship("LicenceAssignment", back_populates="licence", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_software_licences_expiry_date", "expiry_date"),
        Index("ix_software_licences_status", "status"),
        Index("ix_software_licences_is_active", "is_active"),
    )
