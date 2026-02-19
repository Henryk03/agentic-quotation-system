
from typing import Literal
from pydantic import BaseModel

from shared.events.metadata import BaseMetadata


class ClearChatMessagesResultEvent(BaseModel):
    """"""

    type: Literal["chat.clear.messages.result"] = "chat.clear.messages.result"
    metadata: BaseMetadata
    success: bool


class ClearChatMessagesEvent(BaseModel):
    """"""

    type: Literal["chat.clear_messages"] = "chat.clear_messages"
    metadata: BaseMetadata


class DeleteClientChatsResultEvent(BaseModel):
    """"""

    type: Literal["client.chats.delete.result"] = "client.chats.delete.result"
    success: bool


class DeleteClientChatsEvent(BaseModel):
    """"""

    type: Literal["client.clear_chats"] = "client.clear_chats"