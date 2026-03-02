
from sqlalchemy import (
    delete, 
    desc, 
    select
)
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.actions.client_touch import touch_client
from backend.database.models.message import Message


class MessageRepository:
    """
    Repository class for managing messages within chats for clients.
    """
    

    @staticmethod
    async def get_last_user_message(
            db: AsyncSession,
            client_id: str,
            chat_id: str,
        ) -> str | None:
        """
        Retrieve the most recent message sent by a user in a given chat.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database access.

        client_id : str
            The unique identifier of the client.

        chat_id : str
            The unique identifier of the chat.

        Returns
        -------
        str | None
            The content of the last user message if it exists, otherwise None.
        """

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
        """
        Save a message for a client in a specific chat.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database access.

        client_id : str
            The unique identifier of the client.

        chat_id : str
            The unique identifier of the chat.

        role : str
            The role of the sender (e.g., "user" or "assistant").

        content : str
            The message content.

        Returns
        -------
        None
        """

        msg = Message(
            client_id = client_id,
            chat_id = chat_id,
            role = role,
            content = content,
        )

        db.add(msg)

        await touch_client(db, client_id)


    @staticmethod
    async def get_all_messages(
            db: AsyncSession,
            client_id: str,
            chat_id: str
        ) -> list[Message]:
        """
        Retrieve all messages for a client within a specific chat, 
        ordered by creation time ascending.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database access.

        client_id : str
            The unique identifier of the client.

        chat_id : str
            The unique identifier of the chat.

        Returns
        -------
        list[Message]
            A list of Message objects for the specified client 
            and chat.
        """

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
        """
        Delete all messages for a client within a specific chat.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database access.

        client_id : str
            The unique identifier of the client.
            
        chat_id : str
            The unique identifier of the chat.

        Returns
        -------
        None
        """

        await db.execute(
            delete(Message)
            .where(
                Message.client_id == client_id,
                Message.chat_id == chat_id
            )
        )

        await touch_client(db, client_id)