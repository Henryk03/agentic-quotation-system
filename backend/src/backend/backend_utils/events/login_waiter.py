
import asyncio

from fastapi import WebSocket

from backend.backend_utils.events.parser import parse_event

from shared.events import (
    LoginCompletedEvent,
    LoginFailedEvent,
)


async def wait_for_login(
        websocket: WebSocket,
        timeout: int = 60,
    ) -> None:
    """"""

    deadline = asyncio.get_event_loop().time() + timeout

    while True:
        remaining = deadline - asyncio.get_event_loop().time()

        if remaining <= 0:
            raise TimeoutError("Login timeout")

        try:
            raw: dict = await asyncio.wait_for(
                websocket.receive(),
                timeout=remaining,
            )

        except asyncio.TimeoutError:
            raise TimeoutError("Login timeout")

        raw_type = raw.get("type")

        if raw_type != "websocket.receive":
            continue

        raw_text = raw.get("text")
        
        if not raw_text:
            continue

        event = parse_event(raw_text)

        # login completed
        if isinstance(event, LoginCompletedEvent):
            return

        # login failed
        if isinstance(event, LoginFailedEvent):
            raise RuntimeError(
                event.reason or "Login failed"
            )