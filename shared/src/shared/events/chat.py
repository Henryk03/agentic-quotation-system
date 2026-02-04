
from typing import Literal
from pydantic import BaseModel


class ChatMessageEvent(BaseModel):
    """"""
    
    event: Literal["chat.message"] = "chat.message"
    role: Literal["user", "assistant", "tool"]
    content: str
    metadata: dict[str, list[str] | str] | None = None


class ChatCreatedEvent(BaseModel):
    """"""

    event: Literal["chat.created"] = "chat.created"
    chat_id: str