
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class LoginContext(Base):
    """"""

    __tablename__ = "login_contexts"

    client_id: Mapped[str] = mapped_column(
        ForeignKey(
            "clients.client_id", 
            ondelete = "CASCADE"
        ),
        primary_key = True
    )

    store: Mapped[str] = mapped_column(
        String,
        primary_key = True
    )

    current_attemps: Mapped[int] = mapped_column(
        Integer,
        default = 0,
        nullable = False
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
        default = 3,
        nullable = False
    )

    cooldown_seconds: Mapped[int] = mapped_column(
        Integer,
        default = 900,
        nullable = False
    )

    last_error_message: Mapped[str | None] = mapped_column(
        String,
        nullable = True
    )

    last_error_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone = True),
        nullable = True
    )

    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone = True),
        nullable = True
    )

    context_data: Mapped[str | None] = mapped_column(
        String, 
        nullable = True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = lambda: datetime.now(timezone.utc),
        onupdate = lambda: datetime.now(timezone.utc),
        nullable = False
    )

    client = relationship(
        "Client",
        back_populates = "login_contexts",
    )

    attempts = relationship(
        "LoginAttempt",
        back_populates = "context",
        cascade = "all, delete-orphan"
    )