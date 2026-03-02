
from pydantic import BaseModel

from shared.events import Event


class EventEnvelope(BaseModel):
    """
    Wrapper for sending events with associated client information.

    Attributes
    ----------
    client_id : str
        Unique identifier of the client sending the event.
        
    event : Event
        The event object being sent, must be an instance of a 
        subclass of Event.
    """

    client_id: str
    event: Event