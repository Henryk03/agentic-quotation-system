
from shared.events.chat import ChatMessageEvent


def decompose_chat_event(event: ChatMessageEvent) -> tuple[str, dict]:
    """"""

    message = event.content
    metadata = event.metadata

    return message, metadata