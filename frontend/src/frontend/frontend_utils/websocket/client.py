
import asyncio
import logging
from typing import Callable

import websockets
from websockets import ClientConnection
from playwright.async_api import StorageState

from frontend.frontend_utils.browser.manual_login import run_manual_login
from frontend.frontend_utils.events.converter import to_chat_message_event
from frontend.frontend_utils.websocket.protocol import (
    receive_events,
    receive_credentials_ack
)

from shared.events import Event
from shared.events.login import (
    LoginResultEvent,
    AutoLoginCredentialsEvent
)


class WSClient:
    """"""


    def __init__(
            self,
            websocket: ClientConnection | None,
            session_id: str,
            websocket_uri: str,
            logger: logging.Logger = logging.getLogger("agent-frontend")
        ) -> None:
        """"""

        self.websocket = websocket
        self.session_id = session_id
        self.websocket_uri = websocket_uri
        self.logger = logger

    
    async def connect(
            self
        ) -> ClientConnection:
        """"""

        ws_uri = self.websocket_uri
        s_id = self.session_id
        
        # inserire la lingua nell'.env al setup

        url = f"{ws_uri}?session={s_id}"

        for _ in range(2):
            try:
                ws = await websockets.connect(url)
                await asyncio.sleep(0.2)

                self.logger.info(f"successfully connected at {ws_uri}")

                return ws
            
            except:
                await asyncio.sleep(2)

        self.logger.error(f"connection to {ws_uri} failed")

        raise Exception("Unable to connect to server")


    async def get_websocket(
            self
        ) -> ClientConnection:
        """"""

        self.logger.debug("connecting to server...")

        ws = self.websocket

        if ws is None or ws.close_code is not None:
            ws = await self.connect()

            self.websocket = ws

        else:
            self.logger.debug("already connected")

        return ws
    

    async def ensure_alive(
            self, 
            websocket: ClientConnection,
            timeout: float = 2.0
        ) -> bool:
        """"""

        try:
            pong = await websocket.ping()
            await asyncio.wait_for(pong, timeout)
            return True

        except:
            return False
        

    async def __get_active_websocket(
            self
        ) -> ClientConnection:
        """"""

        ws: ClientConnection = await self.get_websocket()

        if not await self.ensure_alive(ws):
            self.websocket = None

            ws = await self.get_websocket()

        return ws
    

    async def send(
            self,
            role: str,
            message: str,
            metadata: dict[str, list[str] | str],
            on_event: Callable[[Event], bool],
            on_error: Callable[[Exception], None] | None = None
        ) -> bool:
        """"""

        ws: ClientConnection = await self.__get_active_websocket()

        event: Event = to_chat_message_event(role, message, metadata)

        await ws.send(event.model_dump_json())
        received: bool = await receive_events(ws, on_event, on_error)

        return received


    async def send_event(
            self,
            event: Event
        ) -> None:
        """"""

        ws: ClientConnection = await self.__get_active_websocket()
        await ws.send(event.model_dump_json())


    async def send_credentials(
            self,
            credentials: dict
        ) -> bool:
        """"""

        ws: ClientConnection = await self.__get_active_websocket()
        
        event: Event = AutoLoginCredentialsEvent(
            event="autologin.credential.provided",
            credentials=credentials
        )

        await ws.send(event.model_dump_json())
        received_ack: bool = await receive_credentials_ack(ws)

        return received_ack

        


    async def handle_login_cancelled(
            self,
            provider: str
        ) -> None:
        """"""

        ws: ClientConnection = await self.__get_active_websocket()
        await ws.send(
            LoginResultEvent(
                event="login.cancelled",
                provider=provider,
                state="LOGIN_CANCELLED",
                reason="Login process cancelled by user"
            )
        )


    async def handle_login(
            self,
            provider: str,
            login_url: str,
            chat_id: str,
            selected_stores: list[str]
        ) -> bool:
        """"""

        metadata: dict = {
            "chat_id": chat_id,
            "selected_stores": selected_stores
        }

        try:
            storage: StorageState | None = await run_manual_login(
                provider,
                login_url
            )

            if storage:
                event: Event = LoginResultEvent(
                    event="login.success",
                    provider=provider,
                    metadata=metadata,
                    state=storage
                )
                await self.send_event(event)
                return True

            else:
                event: Event = LoginResultEvent(
                    event="login.failed",
                    provider=provider,
                    metadata=metadata,
                    state="LOGIN_FAILED"
                )
                await self.send_event(event)
                return False

        except Exception as e:
            await self.send_event(
                LoginResultEvent(
                    event="login.error",
                    provider=provider,
                    metadata=metadata,
                    state="LOGIN_ERROR",
                    reason=str(e)
                )
            )
            return False