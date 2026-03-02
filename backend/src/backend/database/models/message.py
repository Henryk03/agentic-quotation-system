
from datetime import (
    datetime, 
    timezone
)
from sqlalchemy import (
    DateTime, 
    ForeignKey, 
    String, 
    Text
)
from sqlalchemy.orm import (
    Mapped, 
    mapped_column, 
    relationship
)

from backend.database.base import Base


class Message(Base):
    """
    Database model representing a single message in a chat session.

    Attributes
    ----------
    id : int
        Primary key for the message.

    client_id : str
        Foreign key referencing the client who sent the message.

    chat_id : str
        Foreign key referencing the chat this message belongs to.

    role : str
        Role of the sender (e.g., "user" or "assistant").

    content : str
        The textual content of the message.

    created_at : datetime
        Timestamp when the message was created (UTC).
        
    chat : Chat
        SQLAlchemy relationship to the associated chat.
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key = True)

    client_id: Mapped[str] = mapped_column(
        ForeignKey(
            "clients.client_id",
            ondelete = "CASCADE"
        ),
        nullable = False
    )

    chat_id: Mapped[str] = mapped_column(
        ForeignKey(
            "chats.chat_id",
            ondelete = "CASCADE"
        ),
        nullable = False
    )

    role: Mapped[str] = mapped_column(
        String,
        nullable = False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable = False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = lambda: datetime.now(timezone.utc),
        nullable = False
    )

    chat = relationship(
        "Chat",
        back_populates = "messages"
    )