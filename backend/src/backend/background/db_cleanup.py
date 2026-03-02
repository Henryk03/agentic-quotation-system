
import asyncio
from datetime import timedelta
from logging import (
    getLogger, 
    Logger
)

from backend.database.engine import AsyncSessionLocal
from backend.database.repositories import ClientRepository


logger: Logger = getLogger("db-cleaner")


async def cleanup_inactive_clients_task(
        every_seconds: int = 1800,
        inactive_for_hours: int = 24
    ) -> None:
    """
    Periodically delete inactive clients from the database.

    This asynchronous task runs indefinitely, checking for 
    clients that have been inactive for a specified number 
    of hours and removing them from the database. Logs the 
    number of deleted clients.

    Parameters
    ----------
    every_seconds : int, optional
        Interval in seconds between consecutive cleanup 
        runs (default is 1800).

    inactive_for_hours : int, optional
        Threshold of inactivity in hours; clients inactive 
        longer than this will be deleted (default is 24).

    Returns
    -------
    None

    Raises
    ------
    asyncio.CancelledError
        If the task is cancelled while sleeping or performing cleanup.
    """

    inactive_delta: timedelta = timedelta(hours = inactive_for_hours)

    logger.info(
        f"DB cleanup task started "
        f"(every={every_seconds}s, inactive>{inactive_for_hours}h)"
    )

    try:
        while True:
            async with AsyncSessionLocal() as db:
                deleted = await ClientRepository.delete_inactive_clients(
                    db,
                    inactive_for = inactive_delta
                )

                if deleted:
                    logger.info(f"deleted {deleted} inactive client(s)")

                await db.commit()

            await asyncio.sleep(every_seconds)

    except asyncio.CancelledError:
        logger.info("DB cleanup task cancelled")
        raise