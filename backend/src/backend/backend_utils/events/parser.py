
from pydantic import TypeAdapter
from shared.events import Event


event_adapter = TypeAdapter(Event)


def parse_event(event_string: str) -> Event:
    """"""

    return event_adapter.validate_json(event_string)