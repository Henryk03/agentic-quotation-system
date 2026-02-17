
from typing import Union

from shared.events.credentials import (
    CredentialsValidationResultEvent,
    StoreCredentialsEvent
)
from shared.events.job_status import JobStatusEvent
from shared.events.chat import ChatMessageEvent
from shared.events.error import ErrorEvent
from shared.events.clear import (
    ClearClientChatsEvent,
    ClearChatMessagesEvent
)


Event = Union[
    StoreCredentialsEvent,
    JobStatusEvent,
    ChatMessageEvent,
    ErrorEvent,
    ClearChatMessagesEvent,
    ClearClientChatsEvent
]