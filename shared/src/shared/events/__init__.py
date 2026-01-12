
from typing import Union

from shared.events.chat import ChatMessageEvent
from shared.events.error import ErrorEvent
from shared.events.auth import (
    LoginCompletedEvent,
    LoginFailedEvent,
    LoginRequiredEvent
)


Event = Union[
    ChatMessageEvent,
    LoginRequiredEvent,
    LoginCompletedEvent,
    LoginFailedEvent,
    ErrorEvent
]