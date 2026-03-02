
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


class Chat(Base):
    """
    Database model representing a chat session for 
    a client.

    Attributes
    ----------
    chat_id : str
        Unique identifier for the chat (primary key).

    client_id : str
        Identifier of the client owning this chat 
        (foreign key to `Client`).

    created_at : datetime
        Timestamp of when the chat was created (UTC).

    client : Client
        SQLAlchemy relationship to the owning client.
        
    messages : list[Message]
        SQLAlchemy relationship to the messages in this chat, 
        with cascading delete behavior.
    """

    __tablename__ = "chats"

    chat_id: Mapped[str] = mapped_column(
        String,
        primary_key = True
    )

    client_id: Mapped[str] = mapped_column(
        ForeignKey(
            "clients.client_id",
            ondelete = "CASCADE"
        ),
        nullable = False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = lambda: datetime.now(timezone.utc),
        nullable = False
    )

    client = relationship(
        "Client", 
        back_populates = "chats"
    )

    messages = relationship(
        "Message", 
        back_populates = "chat", 
        cascade = "all, delete-orphan"
    )