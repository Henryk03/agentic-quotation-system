
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from backend.database.actions.job_touch import touch_job
from backend.database.models.job import Job

from shared.shared_utils.common import JobStatus


class JobRepository:
    """
    Repository class for managing jobs for clients and chats.
    """


    @staticmethod
    async def create_job(
            db: AsyncSession, 
            client_id: str,
            chat_id: str | None
        ) -> str:
        """
        Create a new job entry in the database.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database access.

        client_id : str
            The unique identifier of the client creating the job.

        chat_id : str | None
            The ID of the chat associated with the job, if any.

        Returns
        -------
        str
            The unique ID of the newly created job.
        """

        job_id: str = str(uuid.uuid4())

        job = Job(
            id = job_id, 
            client_id = client_id, 
            chat_id = chat_id,
            status = JobStatus.PENDING
        )

        db.add(job)

        await touch_job(db, job_id)

        return job_id


    @staticmethod
    async def set_running(
            db: AsyncSession, 
            job_id: str
        ) -> None:
        """
        Mark a job as running.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for 
            database access.

        job_id : str
            The ID of the job to update.

        Returns
        -------
        None
        """

        job: Job | None = await db.get(Job, job_id)

        if job:
            job.status = JobStatus.RUNNING

            await touch_job(db, job.id)


    @staticmethod
    async def set_result(
            db: AsyncSession, 
            job_id: str, 
            result: dict
        ) -> None:
        """
        Set the result of a completed job and mark it as completed.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database access.

        job_id : str
            The ID of the job to update.

        result : dict
            The result data produced by the job.

        Returns
        -------
        None
        """

        job: Job | None = await db.get(Job, job_id)

        if job:
            job.status = JobStatus.COMPLETED
            job.result = result

            await touch_job(db, job.id)


    @staticmethod
    async def set_error(
            db: AsyncSession, 
            job_id: str, 
            error: str
        ) -> None:
        """
        Mark a job as failed and store the associated error message.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database access.

        job_id : str
            The ID of the job to update.

        error : str
            The error message describing the failure.

        Returns
        -------
        None
        """

        job: Job | None = await db.get(Job, job_id)

        if job:
            job.status = JobStatus.FAILED
            job.error = error

            await touch_job(db, job.id)


    @staticmethod
    async def get(
            db: AsyncSession, 
            job_id: str
        ) -> dict[str, Any] | None:
        """
        Retrieve a job's details by its ID.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database access.
            
        job_id : str
            The ID of the job to retrieve.

        Returns
        -------
        dict[str, Any] | None
            A dictionary containing job details (status, result, 
            error, timestamps) if the job exists, otherwise None.
        """

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