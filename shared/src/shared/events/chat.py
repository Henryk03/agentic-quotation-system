
from typing import Literal
from pydantic import BaseModel


class ChatMessageEvent(BaseModel):
    """"""
    
    type: Literal["chat.message"] = "chat.message"
    role: Literal["user", "assistant", "tool"]
    content: str
    metadata: dict[str, list[str] | str | int] | None = None