
from sqlalchemy import String, DateTime, func
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
        DateTime, 
        server_default=func.now()
    )

    last_active: Mapped[str] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        onupdate=func.now()
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