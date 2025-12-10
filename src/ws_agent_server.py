
import uuid
import uvicorn
import asyncio
from utils import ConnectionManager
from main_agent import run_agent
from fastapi import (
    WebSocket,
    WebSocketDisconnect,
    FastAPI
)


app = FastAPI()
manager = ConnectionManager()


@app.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    """"""

    await manager.connect(ws)
    session_id = ws.query_params.get("session")

    if session_id is None:
        session_id = str(uuid.uuid4())

    try:
        while True:
            try:
                user_message = await asyncio.wait_for(
                    ws.receive_text(),
                    timeout=30
                )

                assistant_reply = await run_agent(
                    user_message,
                    session_id
                )

                await ws.send_text(assistant_reply)

            except asyncio.TimeoutError:
                continue

    except WebSocketDisconnect:
        manager.disconnect(ws)

    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(ws)


async def main():
    config = uvicorn.Config(
        "ws_agent_server:app",
        host="0.0.0.0",
        port=8080
    )
    server = uvicorn.Server(config)

    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())