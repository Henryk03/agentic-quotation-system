
import asyncio
import logging

import uvicorn
from fastapi import WebSocket, FastAPI
from contextlib import asynccontextmanager


from backend.backend_utils.events.parser import parse_event
from backend.backend_utils.events.handler import EventHandler

from backend.backend_utils.connection.connection_manager import ConnectionManager

from backend.database.engine import SessionLocal
from backend.database.repositories import (
    client_repo,
    chat_repo,
    message_repo,
    credential_repo
)


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

    manager = app.state.manager

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
    session_id = ws.query_params.get("session")

    try:
        while True:
            try:
                raw: dict = await asyncio.wait_for(
                    ws.receive(),
                    timeout=5.0
                )

                raw_type = raw.get("type")

                if raw_type == "websocket.receive":
                    if "text" in raw:
                        str_event = raw.get("text")
                        event = parse_event(str_event)

                        with SessionLocal() as db:
                            EventHandler.handle_event(
                                db,
                                event,
                                session_id
                            )

                    else:
                        pass

                elif raw_type == "websocket.disconnect":
                    # logging websocket's auto-disconnect
                    conn_id = manager.get_connection_id(ws)
                    logger.info(f"connection {conn_id} closed")
                    break

            except asyncio.TimeoutError:
                continue

    except Exception as e:
        logger.error(f"websocket error: {e}")
    
    finally:
        await manager.disconnect(ws)


async def start_server(host: str, port: str) -> None:
    """"""
    
    config = uvicorn.Config(
        "backend.server.websocket_server:app",
        host=host,
        port=port,
        log_config=None,
        log_level="critical",
        lifespan="on"
    )

    print("📣 Ready for connections (Press Ctrl+C to stop)")

    server = uvicorn.Server(config)
    await server.serve()