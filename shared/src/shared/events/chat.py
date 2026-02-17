
from typing import Literal
from pydantic import BaseModel

from shared.events.metadata import StoreMetadata


class ChatMessageEvent(BaseModel):
    """"""
    
    type: Literal["chat.message"] = "chat.message"
    role: Literal["user", "assistant", "tool"]
    content: str
    metadata: StoreMetadata | None