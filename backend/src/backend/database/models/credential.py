
from sqlalchemy import (
    Boolean, 
    ForeignKey, 
    String
)
from sqlalchemy.orm import (
    Mapped, 
    mapped_column, 
    relationship
)

from backend.database.base import Base


class Credential(Base):
    """
    Database model representing credentials for a specific store 
    associated with a client.

    Attributes
    ----------
    client_id : str
        Foreign key referencing the associated client.

    store : str
        Name of the store or provider for these credentials.

    username : str
        Username used to log into the store.

    password : str
        Password used to log into the store.

    is_valid : bool
        Flag indicating whether the credentials are currently valid.
        
    client : Client
        SQLAlchemy relationship to the associated client.
    """

    __tablename__ = "credentials"

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

    username: Mapped[str] = mapped_column(
        String,
        nullable = False
    )

    password: Mapped[str] = mapped_column(
        String,
        nullable = False
    )

    is_valid: Mapped[bool] = mapped_column(
        Boolean, 
        default = True
    )

    client = relationship(
        "Client",
        back_populates = "credentials"
    )