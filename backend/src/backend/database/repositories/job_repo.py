
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from backend.database.actions.job_touch import touch_job
from backend.database.models.job import Job

from shared.shared_utils.common import JobStatus


class JobRepository:
    """"""


    @staticmethod
    async def create_job(
            db: AsyncSession, 
            client_id: str,
            chat_id: str | None
        ) -> str:
        """"""

        job_id: str = str(uuid.uuid4())

        job = Job(
            id = job_id, 
            client_id = client_id, 
            chat_id = chat_id,
            status = JobStatus.PENDING
        )

        db.add(job)

        await touch_job(db, job_id)
        await db.commit()

        return job_id


    @staticmethod
    async def set_running(
            db: AsyncSession, 
            job_id: str
        ) -> None:
        """"""

        job: Job | None = await db.get(Job, job_id)

        if job:
            job.status = JobStatus.RUNNING

            await touch_job(db, job.id)
            await db.commit()


    @staticmethod
    async def set_result(
            db: AsyncSession, 
            job_id: str, 
            result: dict
        ) -> None:
        """"""

        job: Job | None = await db.get(Job, job_id)

        if job:
            job.status = JobStatus.COMPLETED
            job.result = result

            await touch_job(db, job.id)
            await db.commit()


    @staticmethod
    async def set_error(
            db: AsyncSession, 
            job_id: str, 
            error: str
        ) -> None:
        """"""

        job: Job | None = await db.get(Job, job_id)

        if job:
            job.status = JobStatus.FAILED
            job.error = error

            await touch_job(db, job.id)
            await db.commit()


    @staticmethod
    async def get(
            db: AsyncSession, 
            job_id: str
        ) -> dict[str, Any] | None:
        """"""

        job: Job | None = await db.get(Job, job_id)

        if job:
            return {
                "job_id": job.id,
                "client_id": job.client_id,
                "chat_id": job.chat_id,
                "status": job.status,
                "result": job.result,
                "error": job.error,
                "created_at": str(job.created_at),
                "updated_at": str(job.updated_at)
            }
        
        return None