
from datetime import (
    datetime, 
    timezone
)
from sqlalchemy import (
    DateTime, 
    String
)
from sqlalchemy.orm import (
    Mapped, 
    mapped_column, 
    relationship
)

from backend.database.base import Base


class Client(Base):
    """
    Database model representing a client in the system.

    Attributes
    ----------
    client_id : str
        Unique identifier for the client (primary key).

    created_at : datetime
        Timestamp of when the client was created (UTC).

    last_active : datetime
        Timestamp of the client's last activity, updated 
        automatically (UTC).

    chats : list[Chat]
        SQLAlchemy relationship to the chats associated 
        with this client, with cascading delete behavior.

    credentials : list[Credential]
        SQLAlchemy relationship to the client's credentials,
        with cascading delete behavior.

    login_contexts : list[LoginContext]
        SQLAlchemy relationship to the client's login contexts,
        with cascading delete behavior.
        
    jobs : list[Job]
        SQLAlchemy relationship to the jobs associated with 
        this client, with cascading delete behavior.
    """

    __tablename__ = "clients"

    client_id: Mapped[str] = mapped_column(
        String, 
        primary_key = True
    )

    created_at: Mapped[str] = mapped_column(
        DateTime(timezone = True),
        default = lambda: datetime.now(timezone.utc),
        nullable = False
    )

    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = lambda: datetime.now(timezone.utc),
        onupdate = lambda: datetime.now(timezone.utc),
        nullable = False
    )

    chats = relationship(
        "Chat", 
        back_populates = "client", 
        cascade = "all, delete-orphan"
    )

    credentials = relationship(
        "Credential", 
        back_populates = "client", 
        cascade = "all, delete-orphan"
    )

    login_contexts = relationship(
        "LoginContext",
        back_populates = "client",
        cascade = "all, delete-orphan",
    )
    
    jobs = relationship(
        "Job", 
        back_populates = "client", 
        cascade = "all, delete-orphan"
    )