
from pydantic import TypeAdapter

from shared.events import Event


event_adapter = TypeAdapter(Event)

def parse_event(raw_event: str) -> Event:
    """"""

    return event_adapter.validate_json(raw_event)

