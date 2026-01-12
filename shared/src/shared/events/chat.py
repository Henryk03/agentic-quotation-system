
from typing import Literal
from pydantic import BaseModel


class ChatMessageEvent(BaseModel):
    """"""
    
    event: Literal["chat.message"] = "chat.message"
    role: Literal["user", "assistant", "tool"]
    content: str