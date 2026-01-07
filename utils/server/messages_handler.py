
import json
from fastapi import WebSocket
from langchain.messages import AIMessage, ToolMessage


async def handle_message(
        websocket: WebSocket,
        message: str
    ) -> None:
    """"""

    if isinstance(message, AIMessage):
        pass
    elif isinstance(message, ToolMessage):
        pass
    elif message

