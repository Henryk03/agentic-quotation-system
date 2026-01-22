
import uuid
from logging import Logger

from fastapi import WebSocket
from starlette.datastructures import Address
from fastapi.websockets import WebSocketState


class ConnectionManager:
    """"""

    def __init__(
            self, 
            logger: Logger
        ):

        self.logger = logger
        self.active_connections: dict[str, WebSocket] = {}

    
    def get_active(self) -> list[WebSocket]:
        """"""

        return list(self.active_connections.values())
    

    def get_connection_id(
            self, 
            websocket: WebSocket
        ) -> str | None:
        """"""

        conn_id: str
        ws: WebSocket

        for conn_id, ws in self.active_connections.items():
            if ws is websocket:
                return conn_id
            
        return None


    async def connect(
            self, 
            websocket: WebSocket
        ) -> None:
        """"""

        client: Address | None = websocket.client

        try:
            await websocket.accept()

        except:
            if client:
                self.logger.exception(
                    f"connection refused: failed to accept websocket from {client.host}"
                )

            return None
        
        conn_id: str = str(uuid.uuid4().hex)
        self.active_connections[conn_id] = websocket

        if client:
            self.logger.info(
                f"connection {conn_id} accepted from {client.host}:{client.port}"
            )

        self.logger.info(
            f"currently active connections: {len(self.get_active())}"
        )


    async def disconnect(
            self, 
            websocket: WebSocket,
            code: int = 1000,
            reason: str | None = None
        ) -> None:
        """"""
        
        conn_id: str | None = self.get_connection_id(websocket)

        if websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.close(code, reason)

                self.logger.info(
                    f"connection {conn_id} successfully closed"
                )
                
            except:
                self.logger.info(
                    f"connection {conn_id} failed to close"
                )
            
        if conn_id in self.active_connections:
            del self.active_connections[conn_id]

        self.logger.info(
            f"currently active connections: {len(self.get_active())}"
        )