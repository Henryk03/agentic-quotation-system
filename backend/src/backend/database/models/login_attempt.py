
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKeyConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class LoginAttempt(Base):
    """"""

    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key = True,
        autoincrement = True
    )

    client_id: Mapped[str] = mapped_column(
        String,
        nullable = False
    )

    store: Mapped[str] = mapped_column(
        String,
        nullable = False
    )

    success: Mapped[bool] = mapped_column(
        Boolean,
        default = False,
        nullable = False
    )

    reason: Mapped[str | None] = mapped_column(
        String,
        nullable = True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = lambda: datetime.now(timezone.utc),
        nullable = False
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["client_id", "store"],
            ["login_contexts.client_id", "login_contexts.store"],
            ondelete = "CASCADE"
        ),
    )

    context = relationship(
        "LoginContext",
        back_populates = "attempts"
    )