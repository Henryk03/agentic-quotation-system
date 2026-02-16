
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Message(Base):
    """"""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key = True)

    session_id: Mapped[str] = mapped_column(nullable = False)

    chat_id: Mapped[str] = mapped_column(nullable = False)

    role: Mapped[str] = mapped_column(String)

    content: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = lambda: datetime.now(timezone.utc),
        nullable = False
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["chat_id", "session_id"],
            ["chats.chat_id", "chats.session_id"],
            ondelete = "CASCADE"
        ),
        ForeignKeyConstraint(
            ["session_id"],
            ["clients.session_id"],
            ondelete = "CASCADE"
        ),
    )

    chat = relationship(
        "Chat",
        primaryjoin = (
            "and_(Message.chat_id==Chat.chat_id, "
            "Message.session_id==Chat.session_id)"
        ),
        back_populates = "messages"
    )