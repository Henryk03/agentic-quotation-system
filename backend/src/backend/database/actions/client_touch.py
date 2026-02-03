
from datetime import datetime, timezone
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.client import Client


async def touch_client(
        db: AsyncSession,
        session_id: str
    ) -> None:
    """"""
    
    await db.execute(
        update(Client)
        .where(
            Client.session_id == session_id
        )
        .values(
            last_active=datetime.now(timezone.utc)
        )
    )
    await db.commit()