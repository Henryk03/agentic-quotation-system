
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Client(Base):
    """"""

    __tablename__ = "clients"

    session_id: Mapped[str] = mapped_column(
        String, 
        primary_key=True
    )

    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    chats = relationship(
        "Chat", 
        back_populates="client", 
        cascade="all, delete-orphan"
    )
    credentials = relationship(
        "Credential", 
        back_populates="client", 
        cascade="all, delete-orphan"
    )
    browser_contexts = relationship(
        "BrowserContext",
        back_populates="client",
        cascade="all, delete-orphan",
    )