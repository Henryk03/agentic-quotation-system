
from typing import Literal
from pydantic import BaseModel

from shared.events.metadata import BaseMetadata


class ErrorEvent(BaseModel):
    """"""
    
    type: Literal["error.event"] = "error.event"
    message: str
    metadata: BaseMetadata | None = None