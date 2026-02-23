
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.chat import Chat
from backend.database.actions.client_touch import touch_client


class ChatRepository:
    """"""


    @staticmethod
    async def get_or_create_chat(
            db: AsyncSession,
            chat_id: str,
            client_id: str
        ) -> Chat:
        """"""

        chat = await db.get(Chat, chat_id)

        if not chat:
            chat = Chat(
                chat_id = chat_id,
                client_id = client_id
            )
            
            db.add(chat)

            await touch_client(db, client_id)

        return chat


    @staticmethod
    async def delete_all_chats_for_client(
            db: AsyncSession,
            client_id: str
        ) -> None:
        """"""

        await db.execute(
            delete(Chat)
            .where(Chat.client_id == client_id)
        )

        await touch_client(db, client_id)