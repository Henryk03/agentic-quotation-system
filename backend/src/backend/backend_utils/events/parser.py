
from pydantic import TypeAdapter
from shared.events.transport import EventEnvelope


envelope_adapter: TypeAdapter = TypeAdapter(EventEnvelope)


def parse_envelope_from_dict(
        data: dict
    ) -> EventEnvelope:
    """"""

    return envelope_adapter.validate_python(
        data
    )