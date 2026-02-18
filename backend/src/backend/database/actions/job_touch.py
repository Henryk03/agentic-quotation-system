
from datetime import datetime, timezone
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.job import Job


async def touch_job(
        db: AsyncSession,
        job_id: str
    ) -> None:
    """"""
    
    await db.execute(
        update(Job)
        .where(
            Job.id == job_id
        )
        .values(
            updated_at = datetime.now(timezone.utc)
        )
    )
    await db.commit()