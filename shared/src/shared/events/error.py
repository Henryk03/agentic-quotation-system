
from typing import Literal
from pydantic import BaseModel


class ErrorEvent(BaseModel):
    """"""
    
    type: Literal["error"] = "error"
    message: str