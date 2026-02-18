
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from backend.database.actions.client_touch import touch_client
from backend.database.models.client import Client


class ClientRepository:
    """"""
    

    @staticmethod
    async def get_or_create_client(
            db: AsyncSession,
            client_id: str
        ) -> Client:
        """"""

        client: Client | None = await db.get(Client, client_id)

        if not client:
            client = Client(client_id=client_id)
            
            db.add(client)

            await touch_client(db, client_id)
            await db.commit()

        return client


    @staticmethod
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