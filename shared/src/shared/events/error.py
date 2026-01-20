
from typing import Literal
from pydantic import BaseModel


class ErrorEvent(BaseModel):
    """"""
    
    event: Literal["error"] = "error"
    message: str