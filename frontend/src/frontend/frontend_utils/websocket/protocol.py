
import asyncio
from typing import Callable

from websockets import ClientConnection, Data
from websockets.exceptions import ConnectionClosed

from frontend.frontend_utils.events.parser import parse_event

from shared.events import Event
from shared.events.chat import ChatMessageEvent
from shared.events.auth import LoginRequiredEvent


async def receive_events(
        websocket: ClientConnection, 
        on_event: Callable[[Event], bool],
        on_error: Callable[[Exception], None] | None = None,
        timeout: float = 60.0
    ) -> bool:
    """"""
    
    received_any: bool = False

    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    end_time: float = loop.time() + timeout

    event: Event | None = None
    
    try:
        while loop.time() < end_time:
            try:
                raw: Data = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=0.5
                )

            except asyncio.TimeoutError:
                continue
                
            try:
                event = parse_event(str(raw))

            except Exception as e:
                if on_error:
                    on_error(e)

            needs_rerun: bool = on_event(event)
                
            if needs_rerun:
                received_any = True
            
            if event:    
                break

    except ConnectionClosed:
        raise
    
    return received_any