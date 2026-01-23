
from sqlalchemy import String, Text, DateTime, ForeignKeyConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Message(Base):
    """"""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    session_id: Mapped[str] = mapped_column(nullable=False)

    chat_id: Mapped[str] = mapped_column(nullable=False)

    role: Mapped[str] = mapped_column(String)

    content: Mapped[str] = mapped_column(Text)

    created_at: Mapped[str] = mapped_column(
        DateTime, 
        server_default=func.now()
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["chat_id", "session_id"],
            ["chats.chat_id", "chats.session_id"]
        ),
        ForeignKeyConstraint(
            ["session_id"],
            ["clients.session_id"]
        ),
    )

    chat = relationship(
        "Chat",
        primaryjoin=(
            "and_(Message.chat_id==Chat.chat_id, "
            "Message.session_id==Chat.session_id)"
        ),
        back_populates="messages"
    )