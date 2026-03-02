
from datetime import (
    datetime, 
    timezone
)
from sqlalchemy import (
    DateTime, 
    Enum, 
    ForeignKey, 
    JSON, 
    String
)
from sqlalchemy.orm import (
    Mapped, 
    mapped_column, 
    relationship
)

from backend.database.base import Base

from shared.shared_utils.common import JobStatus


class Job(Base):
    """
    Database model representing a background or asynchronous task 
    initiated by a client, optionally linked to a chat.

    Attributes
    ----------
    id : str
        Unique identifier for the job.

    client_id : str
        Foreign key referencing the client who owns the job.

    chat_id : str | None
        Optional foreign key referencing the related chat.

    status : JobStatus
        Current status of the job (e.g., pending, completed, failed).

    result : dict | None
        JSON-serializable object storing the job's result data.

    error : str | None
        Error message if the job failed.

    created_at : datetime
        Timestamp when the job was created (UTC).

    updated_at : datetime
        Timestamp when the job was last updated (UTC).
        
    client : Client
        SQLAlchemy relationship to the associated client.
    """

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