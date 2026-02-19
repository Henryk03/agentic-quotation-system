
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Credential(Base):
    """"""

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