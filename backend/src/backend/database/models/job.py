
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

from shared.shared_utils.common import JobStatus


class Job(Base):
    """"""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String, 
        primary_key = True
    )

    client_id: Mapped[str] = mapped_column(
        ForeignKey(
            "clients.client_id",
            ondelete = "CASCADE"
        )
    )

    chat_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "chats.chat_id",
            ondelete = "CASCADE"
        ),
        nullable = True
    )

    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            name = "job_status",
            native_enum = True
        ),
        default = JobStatus.PENDING,
        nullable = False
    )

    result: Mapped[dict] = mapped_column(
        JSON,
        nullable = True
    )

    error: Mapped[str] = mapped_column(
        String,
        nullable = True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = lambda: datetime.now(timezone.utc),
        nullable = False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = lambda: datetime.now(timezone.utc),
        onupdate = lambda: datetime.now(timezone.utc),
        nullable = False
    )

    client = relationship(
        "Client", 
        back_populates = "jobs"
    )