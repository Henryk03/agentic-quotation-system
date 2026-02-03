
from typing import Any
from datetime import timedelta, datetime, timezone
from sqlalchemy import delete
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.client import Client
from backend.database.actions.client_touch import touch_client


async def get_or_create_client(
        db: AsyncSession,
        session_id: str
    ) -> Client:
    """"""

    client = await db.get(Client, session_id)

    if not client:
        client = Client(session_id=session_id)
        
        db.add(client)

        await touch_client(db, session_id)
        await db.commit()

    return client


async def delete_inactive_clients(
        db: AsyncSession,
        inactive_for: timedelta
    ) -> Any | None:
    """"""

    threshold: datetime = datetime.now(timezone.utc) - inactive_for

    stmt = (
        delete(Client)
        .where(
            Client.last_active < threshold
        )
    )

    result: Result[Any] = await db.execute(stmt)
    deleted: Any | None = getattr(result, "rowcount", None)

    await db.commit()

    return deleted