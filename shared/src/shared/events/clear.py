
from typing import Literal
from pydantic import BaseModel

from shared.events.metadata import BaseMetadata


class ClearChatMessagesEvent(BaseModel):
    """"""

    type: Literal["chat.clear_messages"] = "chat.clear_messages"
    metadata: BaseMetadata


class ClearClientChatsEvent(BaseModel):
    """"""

    type: Literal["client.clear_chats"] = "client.clear_chats"