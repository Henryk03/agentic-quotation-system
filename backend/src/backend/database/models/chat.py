
from sqlalchemy import String, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

class Chat(Base):
    """"""

    __tablename__ = "chats"

    chat_id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    session_id: Mapped[str] = mapped_column(
        ForeignKey("clients.session_id"),
        primary_key=True
    )

    created_at: Mapped[str] = mapped_column(
        DateTime, 
        server_default=func.now()
    )

    client = relationship("Client", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")