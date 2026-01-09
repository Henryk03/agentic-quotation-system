
from typing import Literal
from utils.events.base_event import BaseEvent


class ErrorEvent(BaseEvent):
    """"""
    
    type: Literal["error"] = "error"
    message: str