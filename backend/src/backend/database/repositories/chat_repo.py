

from sqlalchemy import select, update
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


async def mark_needs_rerun(
        db: AsyncSession,
        session_id: str,
        chat_id: str
    ) -> None:
    """"""

    await db.execute(
        update(Chat)
        .where(Chat.session_id == session_id)
        .where(Chat.chat_id == chat_id)
        .values(needs_rerun=True)
    )
    await db.commit()


async def consume_rerun_flag(
        db: AsyncSession,
        session_id: str,
        chat_id: str
    ) -> bool:
    """"""

    stmt = (
        select(Chat.needs_rerun)
        .where(Chat.session_id == session_id)
        .where(Chat.chat_id == chat_id)
    )

    result = await db.execute(stmt)
    needs = result.scalar_one()

    if needs:
        await db.execute(
            update(Chat)
            .where(Chat.session_id == session_id)
            .where(Chat.chat_id == chat_id)
            .values(needs_rerun=False)
        )
        await db.commit()

    return needs