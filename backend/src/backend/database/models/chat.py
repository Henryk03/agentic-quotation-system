
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey
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
        ForeignKey(
            "clients.session_id",
            ondelete="CASCADE"
        ),
        primary_key=True,
    )

    needs_rerun: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    client = relationship(
        "Client", 
        back_populates="chats"
    )
    messages = relationship(
        "Message", 
        back_populates="chat", 
        cascade="all, delete-orphan"
    )