
import asyncio
import logging

import uvicorn
from fastapi import WebSocket, FastAPI
from contextlib import asynccontextmanager

from backend.agent.main_agent import graph as agent
from backend.backend_utils.events.dispatcher import dispatch_chat
from backend.backend_utils.connection.connection_manager import ConnectionManager


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
            raw_message: dict = await asyncio.wait_for(
                ws.receive()
            )

            message_type = raw_message.get("type")

            if message_type == "websocket.receive":
                user_message = raw_message.get("text")

                await dispatch_chat(
                    agent,
                    user_message,
                    session_id,
                    ws
                )

            elif message_type == "websocket.disconnect":
                # logging websocket's auto-disconnect
                conn_id = manager.get_connection_id(ws)
                logger.info(f"connection {conn_id} closed")
                break

    except Exception as e:
        logger.error(f"websocket error: {e}")
    
    finally:
        await manager.disconnect(ws)


async def start_server() -> None:
    """"""
    
    config = uvicorn.Config(
        "websocket_server.websocket_agent_server:app",
        host="0.0.0.0",
        port=8080,
        log_config=None,
        log_level="critical",
        lifespan="on"
    )

    server = uvicorn.Server(config)
    await server.serve()