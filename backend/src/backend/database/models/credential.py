
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Credential(Base):
    """"""

    __tablename__ = "credentials"

    session_id: Mapped[str] = mapped_column(
        ForeignKey(
            "clients.session_id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )

    store: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    username: Mapped[str] = mapped_column(String)

    password: Mapped[str] = mapped_column(String)

    client = relationship(
        "Client",
        back_populates="credentials"
    )