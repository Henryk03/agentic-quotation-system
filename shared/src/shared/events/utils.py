
from shared.events import Event


def extract_chat_id(
        event: Event
    ) -> str | None:
    """"""

    if hasattr(event, "chat_id"):
        return getattr(event, "chat_id")
    
    if hasattr(event, "metadata") and isinstance(event.metadata, dict):
        return event.metadata.get("chat_id")
    
    return None