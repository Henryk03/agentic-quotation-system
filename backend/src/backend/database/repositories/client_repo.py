
from datetime import (
    datetime, 
    timedelta, 
    timezone
)
from sqlalchemy import delete
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from backend.database.actions.client_touch import touch_client
from backend.database.models.client import Client


class ClientRepository:
    """
    Repository class for performing database operations 
    on Client objects.
    """
    

    @staticmethod
    async def get_or_create_client(
            db: AsyncSession,
            client_id: str
        ) -> Client:
        """
        Retrieve a client by ID or create a new one if it does not exist.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database access.

        client_id : str
            The unique identifier of the client to retrieve or create.

        Returns
        -------
        Client
            The retrieved or newly created Client object.
        """


        client: Client | None = await db.get(Client, client_id)

        if not client:
            client = Client(client_id=client_id)
            
            db.add(client)

            await touch_client(db, client_id)

        return client


    @staticmethod
    async def delete_inactive_clients(
            db: AsyncSession,
            inactive_for: timedelta
        ) -> Any | None:
        """
        Delete clients that have been inactive for a specified duration.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database access.
            
        inactive_for : timedelta
            The inactivity period threshold. Clients inactive longer 
            than this duration will be deleted.

        Returns
        -------
        int | None
            The number of clients deleted, or None if not available.
        """

        threshold: datetime = datetime.now(timezone.utc) - inactive_for

        stmt = (
            delete(Client)
            .where(
                Client.last_active < threshold
            )
        )

        result: Result[Any] = await db.execute(stmt)
        deleted: Any | None = getattr(result, "rowcount", None)


        return deleted