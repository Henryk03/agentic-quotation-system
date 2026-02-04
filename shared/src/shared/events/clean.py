
from typing import Literal
from pydantic import BaseModel


class ClearChatMessagesEvent(BaseModel):
    """"""

    event: Literal["chat.clear_messages"] = "chat.clear_messages"
    chat_id: str


class ClearClientChatsEvent(BaseModel):
    """"""

    event: Literal["client.clear_chats"] = "client.clear_chats"