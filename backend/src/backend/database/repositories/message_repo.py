
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.actions.client_touch import touch_client
from backend.database.models.message import Message


class MessageRepository:
    """"""
    

    @staticmethod
    async def get_last_user_message(
            db: AsyncSession,
            client_id: str,
            chat_id: str,
        ) -> str | None:
        """"""

        stmt = (
            select(Message)
            .where(
                Message.client_id == client_id,
                Message.chat_id == chat_id,
                Message.role == "user"
            )
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        
        result = await db.execute(stmt)
        message = result.scalar_one_or_none()

        return message.content if message else None


    @staticmethod
    async def save_message(
            db: AsyncSession, 
            client_id: str, 
            chat_id: str, 
            role: str, 
            content: str
        ) -> None:
        """"""

        msg = Message(
            client_id = client_id,
            chat_id = chat_id,
            role = role,
            content = content,
        )

        db.add(msg)

        await touch_client(db, client_id)
        await db.commit()


    @staticmethod
    async def get_all_messages(
            db: AsyncSession,
            client_id: str,
            chat_id: str
        ) -> list[Message]:
        """"""

        stmt = (
            select(Message)
            .where(
                Message.client_id == client_id,
                Message.chat_id == chat_id
            )
            .order_by(
                Message.created_at.asc()
            )
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())


    @staticmethod
    async def delete_messages_for_chat(
            db: AsyncSession,
            client_id: str,
            chat_id: str
        ) -> None:
        """"""

        await db.execute(
            delete(Message)
            .where(
                Message.client_id == client_id,
                Message.chat_id == chat_id
            )
        )

        await touch_client(db, client_id)
        await db.commit()