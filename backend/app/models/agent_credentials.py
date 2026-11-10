from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class AgentCredential(Base):
    __tablename__ = "agent_credentials"

    id = Column(Integer, primary_key=True, index=True)
    computer_id = Column(Integer, ForeignKey("computers.id", ondelete="CASCADE"), nullable=False, index=True)
    key_hash = Column(String(255), nullable=False)  # bcrypt hash of the plaintext API key
    label = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    computer = relationship("Computer", back_populates="agent_credentials")

    __table_args__ = (
        Index("ix_agent_credentials_computer_id", "computer_id"),
        Index("ix_agent_credentials_is_active", "is_active"),
    )
