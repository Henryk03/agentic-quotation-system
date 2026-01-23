
import asyncio
import logging
from typing import Any

from uvicorn import Config, Server
from starlette.types import Message
from fastapi import WebSocket, FastAPI
from contextlib import asynccontextmanager


from backend.backend_utils.events.parser import parse_event
from backend.backend_utils.events.handler import EventHandler
from backend.backend_utils.connection.connection_manager import ConnectionManager
from backend.database.engine import AsyncSessionLocal

from shared.events import Event


logger = logging.getLogger("agent-server")
LOGGER_FORMAT = "%(levelname)s:     %(message)s"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """"""

    logging.basicConfig(level=logging.INFO, format=LOGGER_FORMAT)
    logger.info("server started")

    app.state.manager = ConnectionManager(logger)

    yield

    logger.info("server shutting down...")

    manager: ConnectionManager = app.state.manager

    for ws in manager.get_active():
        try:
            await manager.disconnect(
                ws,
                code=1001,
                reason="server shutdown"
            )
            
        except:
            pass

    logger.info("shutdown complete")


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket) -> None:
    """"""

    manager: ConnectionManager = app.state.manager

    await manager.connect(ws)
    session_id: str = ws.query_params.get("session") or ""

    if session_id == "":
        await manager.disconnect(ws, reason="No Session ID found")

    try:
        while True:
            try:
                raw: Message = await asyncio.wait_for(
                    ws.receive(),
                    timeout=5.0
                )

                raw_type: Any | None = raw.get("type")

                if raw_type == "websocket.receive":
                    if "text" in raw:
                        str_event: Any | None = raw.get("text")
                        event: Event = parse_event(str(str_event))

                        async with AsyncSessionLocal() as db:
                            await EventHandler.handle_event(
                                db,
                                event,
                                session_id,
                                ws
                            )

                    else:
                        pass

                elif raw_type == "websocket.disconnect":
                    # logging websocket's auto-disconnect
                    conn_id: str | None = manager.get_connection_id(ws)
                    logger.info(f"connection {conn_id} closed")
                    break

            except asyncio.TimeoutError:
                continue

    except Exception as e:
        logger.error(f"websocket error: {e}")
    
    finally:
        await manager.disconnect(ws)


async def start_server(host: str, port: int) -> None:
    """"""
    
    config: Config = Config(
        app="backend.server.websocket_server:app",
        host=host,
        port=port,
        log_config=None,
        log_level="critical",
        lifespan="on"
    )

    print("📣 Ready for connections (Press Ctrl+C to stop)\n")

    server: Server = Server(config)
    await server.serve()