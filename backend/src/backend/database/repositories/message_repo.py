
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.message import Message
from backend.database.actions.client_touch import touch_client


async def get_last_user_message(
        db: AsyncSession,
        session_id: str,
        chat_id: str,
    ) -> str | None:
    """"""

    stmt = (
        select(Message)
        .where(
            Message.session_id == session_id,
            Message.chat_id == chat_id,
            Message.role == "user"
        )
        .order_by(desc(Message.created_at))
        .limit(1)
    )
    
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    return message.content if message else None


async def save_message(
        db: AsyncSession, 
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

    await touch_client(db, session_id)
    await db.commit()


async def get_all_messages(
        db: AsyncSession,
        session_id: str,
        chat_id: str
    ) -> list[Message]:
    """"""

    stmt = (
        select(Message)
        .where(
            Message.session_id == session_id,
            Message.chat_id == chat_id
        )
        .order_by(
            Message.created_at.asc()
        )
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())