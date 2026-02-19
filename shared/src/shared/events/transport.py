
from pydantic import BaseModel

from shared.events import Event


class EventEnvelope(BaseModel):
    """"""

    client_id: str
    event: Event