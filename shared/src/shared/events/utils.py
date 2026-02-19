
from shared.events import Event
from shared.events.metadata import (
    BaseMetadata, 
    StoreMetadata
)


def extract_chat_id(
        event: Event
    ) -> str | None:
    """"""

    if hasattr(event, "chat_id"):
        return getattr(event, "chat_id", None)
    
    metadata: BaseMetadata | StoreMetadata | None = (
        getattr(event, "metadata", None)
    )

    if metadata:
        if hasattr(metadata, "chat_id"):
            return getattr(metadata, "chat_id", None)
        
        if isinstance(metadata, dict):
            return metadata.get("chat_id", None)
    
    return None