
from datetime import (
    datetime, 
    timezone
)
from sqlalchemy import (
    DateTime, 
    ForeignKey, 
    String
)
from sqlalchemy.orm import (
    Mapped, 
    mapped_column, 
    relationship
)

from backend.database.base import Base


class LoginContext(Base):
    """
    Database model storing authentication state for a client 
    on a specific store or provider.

    Attributes
    ----------
    client_id : str
        Foreign key referencing the client associated with 
        this login context.

    store : str
        Name of the store or provider.

    context_data : str | None
        Serialized storage state or authentication data for 
        automatic login.

    updated_at : datetime
        Timestamp when the context was last updated (UTC).
        
    client : Client
        SQLAlchemy relationship to the associated client.
    """

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