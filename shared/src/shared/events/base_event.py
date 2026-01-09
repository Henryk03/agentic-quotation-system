
import json
from pydantic import BaseModel


class BaseEvent(BaseModel):
    """"""
    
    type: str

    def to_json_str(self) -> str:
        """"""

        return self.model_dump_json()