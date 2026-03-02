
from pydantic import BaseModel
from typing import Literal

from shared.events.metadata import BaseMetadata


class ClearChatMessagesResultEvent(BaseModel):
    """
    Event requesting the removal of all messages from a specific chat.

    Attributes
    ----------
    type : Literal["chat.clear_messages"]
        Discriminator identifying the event type. Always set to
        `"chat.clear_messages"`.

    metadata : BaseMetadata
        Metadata containing contextual information about the chat,
        typically including the `chat_id` of the conversation
        to be cleared.

    Notes
    -----
    This event is sent from the frontend to the backend to trigger
    deletion of messages for a single chat session.
    """

    type: Literal["chat.clear.messages.result"] = "chat.clear.messages.result"
    metadata: BaseMetadata
    success: bool


class ClearChatMessagesEvent(BaseModel):
    """
    Event representing the result of a chat message clearing operation.

    Attributes
    ----------
    type : Literal["chat.clear.messages.result"]
        Discriminator identifying the event type. Always set to
        `"chat.clear.messages.result"`.

    metadata : BaseMetadata
        Metadata associated with the original request, containing 
        the `chat_id`.

    success : bool
        Indicates whether the chat messages were successfully cleared.

    Notes
    -----
    This event is returned by the backend in response to a
    `ClearChatMessagesEvent`.
    """

    type: Literal["chat.clear_messages"] = "chat.clear_messages"
    metadata: BaseMetadata


class DeleteClientChatsResultEvent(BaseModel):
    """
    Event requesting the deletion of all chats associated with a client.

    Attributes
    ----------
    type : Literal["client.clear_chats"]
        Discriminator identifying the event type. Always set to
        `"client.clear_chats"`.

    Notes
    -----
    This event removes all chat sessions linked to the client,
    effectively resetting the conversation history.
    """

    type: Literal["client.chats.delete.result"] = "client.chats.delete.result"
    success: bool


class DeleteClientChatsEvent(BaseModel):
    """
    Event representing the result of a client chat deletion request.

    Attributes
    ----------
    type : Literal["client.chats.delete.result"]
        Discriminator identifying the event type. Always set to
        `"client.chats.delete.result"`.

    success : bool
        Indicates whether the client chats were successfully deleted.

    Notes
    -----
    This event is returned by the backend after processing a
    `DeleteClientChatsEvent`.
    """

    type: Literal["client.clear_chats"] = "client.clear_chats"