
import uvicorn
import asyncio
import logging
from src.main_agent import run_agent
from fastapi import WebSocket, FastAPI
from contextlib import asynccontextmanager
from utils.browser.connection_manager import ConnectionManager
from utils.provider.base_provider import BaseProvider


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


async def notify_ui_login_event(
        websocket: WebSocket,
        payload: dict
    ) -> None:
    """"""

    await websocket.send_json(payload)


@app.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket) -> None:
    """"""

    manager: ConnectionManager = app.state.manager

    await manager.connect(ws)
    session_id = ws.query_params.get("session")

    try:
        while True:
            try:
                message = await asyncio.wait_for(
                    ws.receive(),
                    timeout=30
                )

                message_type = message.get("type")

                if message_type == "websocket.receive":
                    if "text" in message:
                        user_message = message["text"]

                        assistant_reply = await run_agent(
                            user_message,
                            session_id,
                            on_login_required=lambda p: notify_ui_login_required(ws, p)
                        )

                        await ws.send_text(assistant_reply)

                    else:
                        pass

                elif message_type == "websocket.disconnect":
                    break

            except asyncio.TimeoutError:
                continue

    except Exception as e:
        logger.error(f"websocket error: {e}")
    
    finally:
        await manager.disconnect(ws)


async def main():
    config = uvicorn.Config(
        "ws_agent_server:app",
        host="0.0.0.0",
        port=8080,
        log_config=None,
        log_level="critical"
    )

    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())