
from typing import Union

from shared.events.error import ErrorEvent
from shared.events.chat import (
    ChatMessageEvent, 
    ChatCreatedEvent
)
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
    ChatMessageEvent,
    ChatCreatedEvent,
    LoginRequiredEvent,
    LoginResultEvent,
    AutoLoginCredentialsEvent,
    ErrorEvent,
    ClearChatMessagesEvent,
    ClearClientChatsEvent
]