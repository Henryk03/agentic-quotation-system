
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.client import Client


async def get_or_create_client(
        db: AsyncSession,
        session_id: str
    ) -> Client:
    """"""

    client = await db.get(Client, session_id)

    if not client:
        client = Client(session_id=session_id)
        
        db.add(client)
        await db.commit()
        await db.refresh(client)

    return client