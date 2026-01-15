
from typing import Literal
from pydantic import BaseModel


class InitMetadataEvent(BaseModel):
    """"""

    event: Literal["init.event"] = "init.event"
    metadata: dict