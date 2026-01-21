
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class BrowserContext(Base):
    """"""

    __tablename__ = "browser_contexts"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("client.session_id", ondelete="CASCADE"),
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

    updated_at: Mapped[str] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    client = relationship("Client")