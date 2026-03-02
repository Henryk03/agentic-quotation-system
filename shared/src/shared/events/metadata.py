
from pydantic import BaseModel


class BaseMetadata(BaseModel):
    """
    Base metadata shared across events.

    Attributes
    ----------
    chat_id : str
        Unique identifier of the chat associated with the event.
    """

    chat_id: str


class StoreMetadata(BaseMetadata):
    """
    Metadata for events related to store interactions.

    Inherits from BaseMetadata.

    Attributes
    ----------
    chat_id : str
        Unique identifier of the chat associated with the event.

    selected_stores : list of str
        List of store identifiers selected for the current operation.

    selected_external_store_urls : list of str
        List of custom external store URLs to be used in addition to 
        supported stores.

    items_per_store : int, optional
        Number of items to retrieve per store. Default is 1.
    """

    selected_stores: list[str]
    selected_external_store_urls: list[str]
    items_per_store: int = 1