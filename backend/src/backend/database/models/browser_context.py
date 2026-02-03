
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class BrowserContext(Base):
    """"""

    __tablename__ = "browser_contexts"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("clients.session_id", ondelete="CASCADE"),
        primary_key=True
    )

    store: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    state: Mapped[str] = mapped_column(String)

    fail_reason: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    attempts_history: Mapped[list[dict[str, str]] | None] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    client = relationship(
        "Client",
        back_populates="browser_contexts",
    )