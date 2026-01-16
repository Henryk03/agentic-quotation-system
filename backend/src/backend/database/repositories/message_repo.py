
from sqlalchemy.orm import Session

from backend.database.models.message import Message


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