
from datetime import (
    datetime, 
    timezone
)
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.client import Client


async def touch_client(
        db: AsyncSession,
        client_id: str
    ) -> None:
    """
    Update the last active timestamp of a client in 
    the database.

    This function sets the `last_active` field of the 
    specified client to the current UTC time. It is 
    typically used to mark a client as recently active.

    Parameters
    ----------
    db : AsyncSession
        The SQLAlchemy asynchronous session to use for 
        the update.

    client_id : str
        The unique identifier of the client whose timestamp 
        is to be updated.
    """
    
    await db.execute(
        update(Client)
        .where(
            Client.client_id == client_id
        )
        .values(
            last_active = datetime.now(timezone.utc)
        )
    )