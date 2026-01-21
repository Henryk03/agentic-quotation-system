
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.database.models.message import Message


def get_last_user_message(
        db: Session,
        sessio_id: str,
        chat_id: str,
    ) -> str | None:
    """"""

    message = (
        db.query(Message)
        .filter(
            Message.sessio_id == sessio_id,
            Message.chat_id == chat_id,
            Message.role == "user"
        )
        .order_by(
            desc(Message.created_at)
        )
        .first()
    )

    return message.content if message else None


def save_message(
        db: Session, 
        session_id: str, 
        chat_id: str, 
        role: str, 
        content: str
    ) -> None:
    """"""

    msg = Message(
        session_id=session_id,
        chat_id=chat_id,
        role=role,
        content=content,
    )

    db.add(msg)
    db.commit()