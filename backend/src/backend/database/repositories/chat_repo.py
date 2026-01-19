
from sqlalchemy.orm import Session

from backend.database.models.chat import Chat


def get_or_create_chat(
        db: Session,
        chat_id: str,
        session_id: str
    ) -> Chat:
    """"""

    chat = db.get(Chat, (chat_id, session_id))

    if not chat:
        chat = Chat(
            chat_id=chat_id,
            session_id=session_id
        )
        
        db.add(chat)
        db.commit()

    return chat