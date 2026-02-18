
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKeyConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Message(Base):
    """"""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key = True)

    client_id: Mapped[str] = mapped_column(nullable = False)

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
            ["chat_id", "client_id"],
            ["chats.chat_id", "chats.client_id"],
            ondelete = "CASCADE"
        ),
        ForeignKeyConstraint(
            ["client_id"],
            ["clients.client_id"],
            ondelete = "CASCADE"
        ),
    )

    chat = relationship(
        "Chat",
        primaryjoin = (
            "and_(Message.chat_id==Chat.chat_id, "
            "Message.client_id==Chat.client_id)"
        ),
        back_populates = "messages"
    )