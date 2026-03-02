
import asyncio
from datetime import datetime
from logging import (
    basicConfig,
    getLogger,
    Logger
)

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from uvicorn import Config, Server

from backend.config import settings
from backend.backend_utils.events.handler import EventHandler
from backend.background.db_cleanup import cleanup_inactive_clients_task
from backend.database.engine import AsyncSessionLocal
from backend.database.repositories import (
    ChatRepository,
    ClientRepository,
    JobRepository
)

from shared.events import Event
from shared.events.error import ErrorEvent
from shared.events.job_status import JobStatusEvent
from shared.events.metadata import BaseMetadata
from shared.events.transport import EventEnvelope
from shared.events.utils import extract_chat_id
from shared.shared_utils.common import JobStatus


logger: Logger = getLogger("agent-server")
LOGGER_FORMAT = "%(levelname)s | %(asctime)s | %(message)s"


@asynccontextmanager
async def lifespan(
        app: FastAPI
    ):
    """
    Async context manager for the FastAPI application lifespan.

    Initializes logging, sets the server timezone, and starts 
    the background task for cleaning up inactive clients. 
    Ensures graceful shutdown by cancelling the background task.

    Parameters
    ----------
    app : FastAPI
        The FastAPI application instance.

    Yields
    ------
    None
    """

    basicConfig(
        level = settings.LOG_LEVEL, 
        format = LOGGER_FORMAT,
        datefmt = "%Y-%m-%d %H:%M:%S"
    )

    logger.info("server started")

    app.state.timezone = datetime.now().astimezone().tzinfo

    logger.info(f"server timezone: {app.state.timezone}")

    cleanup_task: asyncio.Task = asyncio.create_task(
        cleanup_inactive_clients_task(
            every_seconds = 1800,
            inactive_for_hours = 24
        )
    )

    try:
        yield

    finally:
        logger.info("server shutting down...")

        cleanup_task.cancel()

        try:
            await cleanup_task

        except asyncio.CancelledError:
            pass

        logger.info("shutdown complete")


app: FastAPI = FastAPI(lifespan = lifespan)


@app.post("/event")
async def create_event_job(
        envelope: EventEnvelope
    ) -> dict[str, str]:
    """
    Endpoint to create a new job for an incoming event.

    The function stores or ensures the existence of the client 
    and chat, creates a job record, and triggers asynchronous 
    processing of the event.

    Parameters
    ----------
    envelope : EventEnvelope
        The wrapper containing the client ID and the event to process.

    Returns
    -------
    dict[str, str]
        Dictionary containing the job status with job ID.
    """

    client_id: str = envelope.client_id
    event: Event = envelope.event

    chat_id: str | None = extract_chat_id(
        event
    )

    job_id: str = ""

    async with AsyncSessionLocal() as db:
        try:
            _ = await ClientRepository.get_or_create_client(
                db,
                client_id
            )

            if chat_id:
                _ = await ChatRepository.get_or_create_chat(
                    db,
                    chat_id,
                    client_id
                )

            job_id: str = await JobRepository.create_job(
                db,
                client_id,
                chat_id
            )

            await db.commit()

        except:
            await db.rollback()

    asyncio.create_task(
        run_event_job(
            job_id,
            client_id, 
            event
        )
    )

    status_event: JobStatusEvent = JobStatusEvent(
        job_id = job_id,
        status = JobStatus.PENDING
    )

    return status_event.model_dump()


async def run_event_job(
        job_id: str, 
        client_id: str,
        event: Event
    ) -> None:
    """
    Execute the event asynchronously and update job status in 
    the database.

    Processes the event via the EventHandler, sets job status to 
    RUNNING, COMPLETED, or FAILED, and records the results or errors. 
    Commits all changes to the database.

    Parameters
    ----------
    job_id : str
        ID of the job to update.

    client_id : str
        ID of the client associated with the job.

    event : Event
        The event to process.

    Returns
    -------
    None
    """

    async with AsyncSessionLocal() as db:
        try:
            await JobRepository.set_running(
                db,
                job_id
            )
        
            result: dict = await EventHandler.handle_event(
                db,
                event,
                client_id
            )

            await JobRepository.set_result(
                db,
                job_id, 
                result
            )

        except Exception as e:
            await db.rollback()

            metadata: BaseMetadata | None = None

            if getattr(getattr(event, "metadata", None), "chat_id", None):
                metadata = BaseMetadata(
                    chat_id = event.metadata.chat_id
                )

            error_event: Event = ErrorEvent(
                message = str(e),
                metadata = metadata
            )

            await JobRepository.set_error(
                db,
                job_id, 
                str(e)
            )

            await JobRepository.set_result(
                db,
                job_id,
                result = error_event.model_dump()
            )

        await db.commit()


@app.get("/event/{event_id}")
async def get_event_result(
        event_id: str
    ) -> dict:
    """
    Retrieve the result of a previously created job/event.

    Queries the database for the job by ID and returns its 
    current status, result, or error information. Raises 
    HTTP 404 if the job is not found.

    Parameters
    ----------
    event_id : str
        The ID of the event/job to retrieve.

    Returns
    -------
    dict
        Dictionary containing job details including status, 
        result, and timestamps.
    """

    job: dict | None = None

    async with AsyncSessionLocal() as db:
        job = await JobRepository.get(
            db,
            event_id
        )

    if not job:
        raise HTTPException(
            status_code = 404,
            detail = "Event not found"
        )
    
    return job


async def start_server(
        host: str,
        port: int
    ) -> None:
    """
    Start the FastAPI server using Uvicorn programmatically.

    Configures host, port, logging, and lifespan handling, 
    then starts the server asynchronously.

    Parameters
    ----------
    host : str
        Hostname or IP address to bind the server.
        
    port : int
        Port number to bind the server.

    Returns
    -------
    None
    """
    
    config: Config = Config(
        app = "backend.server.rest_server:app",
        host = host,
        port = port,
        log_config = None,
        log_level = "critical",
        lifespan = "on"
    )

    server: Server = Server(config)
    await server.serve()