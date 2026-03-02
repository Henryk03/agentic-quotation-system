
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.chat import Chat
from backend.database.actions.client_touch import touch_client


class ChatRepository:
    """
    Repository class for performing database operations 
    on Chat objects.
    """


    @staticmethod
    async def get_or_create_chat(
            db: AsyncSession,
            chat_id: str,
            client_id: str
        ) -> Chat:
        """
        Retrieve a chat by ID or create a new one if it does not exist.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database access.

        chat_id : str
            The unique identifier of the chat to retrieve or create.

        client_id : str
            The client ID associated with the chat.

        Returns
        -------
        Chat
            The retrieved or newly created Chat object.
        """

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
        """
        Delete all chats associated with a given client.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database access.
            
        client_id : str
            The client ID whose chats should be deleted.

        Returns
        -------
        None
        """

        await db.execute(
            delete(Chat)
            .where(Chat.client_id == client_id)
        )

        await touch_client(db, client_id)