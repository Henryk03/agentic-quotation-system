
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Message(Base):
    """"""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key = True)

    client_id: Mapped[str] = mapped_column(
        ForeignKey(
            "clients.client_id",
            ondelete = "CASCADE"
        ),
        nullable = False
    )

    chat_id: Mapped[str] = mapped_column(
        ForeignKey(
            "chats.chat_id",
            ondelete = "CASCADE"
        ),
        nullable = False
    )

    role: Mapped[str] = mapped_column(String)

    content: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = lambda: datetime.now(timezone.utc),
        nullable = False
    )

    chat = relationship(
        "Chat",
        back_populates = "messages"
    )