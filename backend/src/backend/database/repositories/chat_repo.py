

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.chat import Chat


async def get_or_create_chat(
        db: AsyncSession,
        chat_id: str,
        session_id: str
    ) -> Chat:
    """"""

    chat = await db.get(Chat, (chat_id, session_id))

    if not chat:
        chat = Chat(
            chat_id=chat_id,
            session_id=session_id
        )
        
        db.add(chat)
        await db.commit()
        await db.refresh(chat)

    return chat