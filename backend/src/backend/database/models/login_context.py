
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, JSON, String
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

    attempts_history: Mapped[list[dict] | None] = mapped_column(
        JSON,
        nullable = True,
        default = list
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
        back_populates = "browser_contexts",
    )