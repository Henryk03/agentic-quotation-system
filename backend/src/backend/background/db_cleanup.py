
import asyncio
import logging
from datetime import timedelta

from backend.database.engine import AsyncSessionLocal
from backend.database.repositories import ClientRepository


logger = logging.getLogger("db-cleaner")


async def cleanup_inactive_clients_task(
        every_seconds: int = 1800,
        inactive_for_hours: int = 24
    ) -> None:
    """"""

    inactive_delta = timedelta(hours=inactive_for_hours)

    logger.info(
        f"DB cleanup task started "
        f"(every={every_seconds}s, inactive>{inactive_for_hours}h)"
    )

    try:
        while True:
            async with AsyncSessionLocal() as db:
                deleted = await ClientRepository.delete_inactive_clients(
                    db,
                    inactive_for=inactive_delta
                )

                if deleted:
                    logger.info(f"deleted {deleted} inactive client(s)")

            await asyncio.sleep(every_seconds)

    except asyncio.CancelledError:
        logger.info("DB cleanup task cancelled")
        raise