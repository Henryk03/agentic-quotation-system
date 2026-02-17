
from typing import Literal
from pydantic import BaseModel


class BaseMetadata(BaseModel):
    """"""

    chat_id: str


class StoreMetadata(BaseMetadata):
    """"""

    selected_stores: list[str]
    selected_external_store_urls: list[str]