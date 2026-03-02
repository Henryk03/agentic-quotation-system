
from pydantic import BaseModel
from typing import Literal

from shared.events.metadata import BaseMetadata


class ErrorEvent(BaseModel):
    """
    Event representing an error that occurred during processing.

    Attributes
    ----------
    type : Literal["error.event"]
        Discriminator identifying the event type. Always set to
        `"error.event"`.

    message : str
        Human-readable description of the error.

    metadata : BaseMetadata or None, optional
        Optional metadata providing context for the error, such as
        chat or client identifiers. Default is `None`.

    Notes
    -----
    This event is returned when an operation fails or an exception
    occurs during processing. It can be used by the frontend or
    other consumers to display or log error messages.
    """
    
    type: Literal["error.event"] = "error.event"
    message: str
    metadata: BaseMetadata | None = None