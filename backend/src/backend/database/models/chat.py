
from sqlalchemy import String, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

class Chat(Base):
    """"""

    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True)

    chat_id: Mapped[str] = mapped_column(String)

    session_id: Mapped[str] = mapped_column(
        ForeignKey("clients.session_id")
    )

    created_at: Mapped[str] = mapped_column(
        DateTime, 
        server_default=func.now()
    )

    client = relationship("Client", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("session_id", "chat_id")
    )