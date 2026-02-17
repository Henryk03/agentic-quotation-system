
import asyncio
import logging
import requests
from typing import Callable, Any
from requests import Response
from asyncio import AbstractEventLoop

from playwright.async_api import StorageState
from websockets import (
    ClientConnection, 
    ConnectionClosed
)

from frontend.frontend_utils.browser.manual_login import run_manual_login
from frontend.frontend_utils.events.converter import to_chat_message_event
from frontend.frontend_utils.websocket.protocol import (
    receive_events,
    receive_credentials_ack
)

from shared.events import Event
from shared.events.transport import EventEnvelope


class RESTClient:
    """"""


    def __init__(
            self,
            base_url: str,
            session_id: str
        ) -> None:
        """"""

        self.base_url = base_url.rstrip("/")
        self.session_id = session_id


    def send_event(
            self,
            event: Event
        ) -> str | None:
        """"""

        envelope: EventEnvelope = EventEnvelope(
            session_id = self.session_id,
            event = event
        )

        response: Response = requests.post(
            url = self.base_url,
            json = envelope.model_dump()
        )

        response.raise_for_status()

        data: dict = response.json()

        return data.get("event_id")
    

    def get_job(
            self,
            event_id: str
        ) -> dict[str, Any]:
        """"""

        response: Response = requests.get(
            url = f"{self.base_url}/event/{event_id}"
        )

        response.raise_for_status()

        return response.json()
    

    async def send_and_wait(
            self,
            event: Event,
            poll_interval: float = 0.5,
            timeout: float = 60.0
        ) -> dict | None:
        """"""

        event_id: str | None = self.send_event(event)

        loop: AbstractEventLoop = asyncio.get_event_loop()
        deadline: float = loop.time() + timeout

        if event_id:
            while loop.time() < deadline:
                job_data: dict[str, Any] = self.get_job(event_id)

                status: str = job_data.get("status", "FAILED")

                if status == "COMPLETED":
                    return job_data.get("result")
                
                if status == "FAILED":
                    raise Exception(
                        job_data.get("error", "Something went wrong.")
                    )
                
                await asyncio.sleep(poll_interval)

        raise TimeoutError(f"Timeout waiting for job {event_id}")

    
    # async def connect(
    #         self
    #     ) -> ClientConnection:
    #     """"""

    #     ws_uri = self.websocket_uri
    #     s_id = self.session_id

    #     url = f"{ws_uri}?session={s_id}"

    #     for _ in range(2):
    #         try:
    #             ws = await websockets.connect(url)
    #             await asyncio.sleep(0.2)

    #             self.logger.info(f"successfully connected at {ws_uri}")

    #             return ws
            
    #         except:
    #             await asyncio.sleep(2)

    #     self.logger.error(f"connection to {ws_uri} failed")

    #     raise Exception("Unable to connect to server")


    # async def get_websocket(
    #         self
    #     ) -> ClientConnection:
    #     """"""

    #     self.logger.debug("connecting to server...")

    #     ws = self.websocket

    #     if ws is None or ws.close_code is not None:
    #         ws = await self.connect()

    #         self.websocket = ws

    #     else:
    #         self.logger.debug("already connected")

    #     return ws
    

    # async def ensure_alive(
    #         self, 
    #         websocket: ClientConnection,
    #         timeout: float = 2.0
    #     ) -> bool:
    #     """"""

    #     try:
    #         pong = await websocket.ping()
    #         await asyncio.wait_for(pong, timeout)
    #         return True

    #     except:
    #         return False
        

    # async def __get_active_websocket(
    #         self
    #     ) -> ClientConnection:
    #     """"""

    #     ws: ClientConnection = await self.get_websocket()

    #     if not await self.ensure_alive(ws):
    #         self.websocket = None

    #         ws = await self.get_websocket()

    #     return ws
    

    # async def send(
    #         self,
    #         role: str,
    #         message: str,
    #         metadata: dict[str, list[str] | str | int],
    #         on_event: Callable[[Event], bool],
    #         on_error: Callable[[Exception], None] | None = None
    #     ) -> bool:
    #     """"""

    #     max_retries: int = 3
    #     attempt: int = 0

    #     ws: ClientConnection = await self.__get_active_websocket()

    #     while attempt < max_retries:
    #         try:
    #             event: Event = to_chat_message_event(role, message, metadata)

    #             await ws.send(event.model_dump_json())
    #             received: bool = await receive_events(ws, on_event, on_error)

    #             self.logger.info(f"Abbiamo ricevuto qualcosa? {received}")

    #             return received

    #         except ConnectionClosed:
    #             self.logger.info("WS closed. Reconnecting...")

    #             ws = await self.__get_active_websocket()
    #             attempt += 1

    #         except Exception as e:
    #             if on_error:
    #                 on_error(e)

    #             return False
            
    #     return False


    # async def send_event(
    #         self,
    #         event: Event
    #     ) -> None:
    #     """"""

    #     ws: ClientConnection = await self.__get_active_websocket()
    #     await ws.send(event.model_dump_json())


    # async def send_credentials(
    #         self,
    #         credentials: dict
    #     ) -> bool:
    #     """"""

    #     ws: ClientConnection = await self.__get_active_websocket()
        
    #     event: Event = AutoLoginCredentialsEvent(
    #         event="autologin.credentials.provided",
    #         credentials=credentials
    #     )

    #     await ws.send(event.model_dump_json())
    #     received_ack: bool = await receive_credentials_ack(ws)

    #     return received_ack
    

    # async def send_clear_messages(
    #         self,
    #         chat_id: str
    #     ) -> None:
    #     """"""

    #     event: Event = ClearChatMessagesEvent(
    #         chat_id = chat_id
    #     )

    #     await self.send_event(event)


    # async def send_clear_chats(
    #         self
    #     ) -> None:
    #     """"""

    #     event: Event = ClearClientChatsEvent()
        
    #     await self.send_event(event)
        
        
    # async def handle_login_cancelled(
    #         self,
    #         provider: str,
    #         metadata: dict,
    #         on_event: Callable[[Event], bool],
    #         on_error: Callable[[Exception], None] | None = None
    #     ) -> bool:
    #     """"""

    #     ws: ClientConnection = await self.__get_active_websocket()

    #     event: Event = LoginResultEvent(
    #         event="login.cancelled",
    #         provider=provider,
    #         metadata=metadata,
    #         state="LOGIN_CANCELLED",
    #         reason="Login process cancelled by user"
    #     )
        
    #     await ws.send(event.model_dump_json())
    #     received: bool = await receive_events(ws, on_event, on_error)

    #     return received


    # async def handle_login(
    #         self,
    #         provider: str,
    #         login_url: str,
    #         chat_id: str,
    #         selected_stores: list[str],
    #         on_event: Callable[[Event], bool],
    #         on_error: Callable[[Exception], None] | None = None
    #     ) -> bool:
    #     """"""

    #     metadata: dict = {
    #         "chat_id": chat_id,
    #         "selected_stores": selected_stores
    #     }

    #     try:
    #         storage: StorageState | None = await run_manual_login(
    #             provider,
    #             login_url
    #         )

    #         ws: ClientConnection = await self.__get_active_websocket()

    #         if storage:
    #             event: Event = LoginResultEvent(
    #                 event="login.success",
    #                 provider=provider,
    #                 metadata=metadata,
    #                 state=storage
    #             ) 

    #             await ws.send(event.model_dump_json())

    #             _ = await receive_events(
    #                 ws,
    #                 on_event,
    #                 on_error
    #             )
                
    #             return True

    #         else:
    #             event: Event = LoginResultEvent(
    #                 event="login.failed",
    #                 provider=provider,
    #                 metadata=metadata,
    #                 state="LOGIN_FAILED"
    #             )
    #             await self.send_event(event)

    #             _ =  await receive_events(
    #                 ws,
    #                 on_event,
    #                 on_error
    #             )
                
    #             return False

    #     except Exception as e:
                
    #         return False