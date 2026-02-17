
from typing import Union

from shared.events.transport import EventEnvelope
from shared.events.chat import ChatMessageEvent
from shared.events.error import ErrorEvent
from shared.events.clean import (
    ClearClientChatsEvent,
    ClearChatMessagesEvent
)
from shared.events.login import (
    LoginResultEvent,
    LoginRequiredEvent,
    AutoLoginCredentialsEvent
)


Event = Union[
    EventEnvelope,
    ChatMessageEvent,
    LoginRequiredEvent,
    LoginResultEvent,
    AutoLoginCredentialsEvent,
    ErrorEvent,
    ClearChatMessagesEvent,
    ClearClientChatsEvent
]