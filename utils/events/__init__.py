
from typing import Union
from .error_events import ErrorEvent
from .chat_events import AIMessageEvent, ToolMessageEvent
from .authentication_events import LoginRequiredEvent, LoginCompletedEvent

Event = Union[
    AIMessageEvent,
    ToolMessageEvent,
    LoginRequiredEvent,
    LoginCompletedEvent,
    ErrorEvent,
]