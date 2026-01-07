
from typing import Union
from utils.events.error_events import ErrorEvent
from utils.events.chat_events import AIMessageEvent, ToolMessageEvent
from utils.events.authentication_events import LoginRequiredEvent, LoginCompletedEvent

Event = Union[
    AIMessageEvent,
    ToolMessageEvent,
    LoginRequiredEvent,
    LoginCompletedEvent,
    ErrorEvent,
]