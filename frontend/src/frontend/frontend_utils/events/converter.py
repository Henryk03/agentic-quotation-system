
from shared.events.chat import ChatMessageEvent


def to_chat_message_event(
        role: str,
        message: str,
        metadata: dict[str, list[str]]
    ) -> ChatMessageEvent:
    """"""

    return ChatMessageEvent(
        role=role,
        content=message,
        metadata=metadata
    )