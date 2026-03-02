
from datetime import (
    datetime, 
    timezone
)
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.job import Job


async def touch_job(
        db: AsyncSession,
        job_id: str
    ) -> None:
    """
    Update the `updated_at` timestamp of a job 
    in the database.

    This function sets the `updated_at` field 
    of the specified job to the current UTC time. 
    It is typically used to mark a job as recently 
    modified or processed.

    Parameters
    ----------
    db : AsyncSession
        The SQLAlchemy asynchronous session to use 
        for the update.

    job_id : str
        The unique identifier of the job whose timestamp 
        is to be updated.
    """
    
    await db.execute(
        update(Job)
        .where(
            Job.id == job_id
        )
        .values(
            updated_at = datetime.now(timezone.utc)
        )
    )