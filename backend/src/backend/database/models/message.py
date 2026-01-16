
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Message(Base):
    """"""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    session_id: Mapped[str] = mapped_column(
        ForeignKey("clients.session_id")
    )

    chat_id: Mapped[str] = mapped_column(
        ForeignKey("chats.chat_id")
    )

    role: Mapped[str] = mapped_column(String)

    content: Mapped[str] = mapped_column(Text)

    created_at: Mapped[str] = mapped_column(
        DateTime, 
        server_default=func.now()
    )

    chat = relationship("Chat", back_populates="messages")