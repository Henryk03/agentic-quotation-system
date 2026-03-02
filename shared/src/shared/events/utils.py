
from shared.events import Event
from shared.events.metadata import (
    BaseMetadata, 
    StoreMetadata
)


def extract_chat_id(
        event: Event
    ) -> str | None:
    """
    Extract the chat ID from an event or its metadata.

    Parameters
    ----------
    event : Event
        The event object from which to extract the chat ID. The 
        chat ID can be present either directly on the event or 
        within its metadata.

    Returns
    -------
    str or None
        The extracted chat ID if present, otherwise `None`.

    Notes
    -----
    This function handles events where `chat_id` is an attribute 
    of the event, or stored inside a `BaseMetadata` or `StoreMetadata` 
    object. It also supports cases where metadata is a dictionary.
    """

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