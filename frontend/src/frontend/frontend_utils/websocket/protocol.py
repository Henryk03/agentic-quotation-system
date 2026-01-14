
import asyncio
from typing import Callable

from websockets import ClientConnection
from websockets.exceptions import ConnectionClosed

from frontend.frontend_utils.events.parser import parse_event

from shared.events import Event
from shared.events.chat import ChatMessageEvent


async def receive_events(
        websocket: ClientConnection, 
        on_event: Callable[[Event], None],
        on_error: Callable[[Exception], None] | None = None,
        timeout: float = 5.0
    ) -> bool:
    """"""
    
    received_any = False

    loop = asyncio.get_event_loop()
    end_time = loop.time() + timeout
    
    try:
        while loop.time() < end_time:
            try:
                raw = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=0.5
                )

            except asyncio.TimeoutError:
                continue
                
            try:
                event = parse_event(raw)

            except Exception as e:
                if on_error:
                    on_error(f"Event partse error: {e}")

            needs_rerun = on_event(event)
                
            if needs_rerun:
                received_any = True
            
            if isinstance(event, ChatMessageEvent) and event.role == "assistant":
                break

    except ConnectionClosed:
        raise
    
    return received_any