from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class InstalledSoftware(Base):
    __tablename__ = "installed_software"

    id = Column(Integer, primary_key=True, index=True)
    computer_id = Column(Integer, ForeignKey("computers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Software details
    name = Column(String(500), nullable=False, index=True)
    version = Column(String(255), nullable=True)
    publisher = Column(String(500), nullable=True)
    install_date = Column(Date, nullable=True)
    install_location = Column(String(1000), nullable=True)

    # Discovery metadata
    first_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    computer = relationship("Computer", back_populates="installed_software")

    __table_args__ = (
        Index("ix_installed_software_computer_id", "computer_id"),
        Index("ix_installed_software_name", "name"),
        Index("ix_installed_software_last_seen", "last_seen"),
        Index("ix_installed_software_is_active", "is_active"),
        Index("ix_installed_software_computer_name", "computer_id", "name"),
    )
