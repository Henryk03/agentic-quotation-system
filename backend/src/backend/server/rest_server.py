
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
from shared.events.job_status import JobStatusEvent
from shared.events.transport import EventEnvelope
from shared.events.utils import extract_chat_id
from shared.shared_utils.common import JobStatus


logger: Logger = getLogger("agent-server")
LOGGER_FORMAT = "%(levelname)s | %(asctime)s | %(message)s"


@asynccontextmanager
async def lifespan(
        app: FastAPI
    ):
    """"""

    basicConfig(
        level=settings.LOG_LEVEL, 
        format=LOGGER_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S"
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
    """"""

    session_id: str = envelope.session_id
    event: Event = envelope.event

    chat_id: str | None = extract_chat_id(
        event
    )

    async with AsyncSessionLocal() as db:
        _ = await ClientRepository.get_or_create_client(
            db,
            session_id
        )

        if chat_id:
            _ = await ChatRepository.get_or_create_chat(
                db,
                chat_id,
                session_id
            )

        job_id: str = await JobRepository.create_job(
            db,
            session_id,
            chat_id
        )

    asyncio.create_task(
        run_event_job(
            job_id,
            session_id, 
            event
        )
    )

    status_event: JobStatusEvent = JobStatusEvent(
        job_id = job_id,
        status = "PENDING"
    )

    return status_event.model_dump()


async def run_event_job(
        job_id: str, 
        session_id: str,
        event: Event
    ) -> None:
    """"""

    async with AsyncSessionLocal() as db:
        try:
            await JobRepository.set_running(
                db,
                job_id
            )
        
            result: dict = await EventHandler.handle_event(
                db,
                event,
                session_id
            )

            await JobRepository.set_result(
                db,
                job_id, 
                result
            )

        except Exception as e:
            await JobRepository.set_error(
                db,
                job_id, 
                str(e)
            )


@app.get("/event/{event_id}")
async def get_event_result(
        event_id: str
    ) -> dict:
    """"""

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
    """"""
    
    config: Config = Config(
        app="backend.server.rest_server:app",
        host=host,
        port=port,
        log_config=None,
        log_level="critical",
        lifespan="on"
    )

    print("📣 Ready for connections (Press Ctrl+C to stop)\n")

    server: Server = Server(config)
    await server.serve()