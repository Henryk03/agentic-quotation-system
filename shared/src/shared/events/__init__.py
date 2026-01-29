
from typing import Union

from shared.events.chat import ChatMessageEvent
from shared.events.error import ErrorEvent
from shared.events.login import (
    LoginResultEvent,
    LoginRequiredEvent,
    AutoLoginCredentialsEvent
)


Event = Union[
    ChatMessageEvent,
    LoginRequiredEvent,
    LoginResultEvent,
    AutoLoginCredentialsEvent,
    ErrorEvent
]