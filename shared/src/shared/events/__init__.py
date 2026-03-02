
from typing import Union

from shared.events.chat import ChatMessageEvent
from shared.events.clear import (
    ClearChatMessagesEvent,
    ClearChatMessagesResultEvent,
    DeleteClientChatsEvent,
    DeleteClientChatsResultEvent,
)
from shared.events.credentials import (
    CredentialEntry, 
    StoreCredentialsEvent
)
from shared.events.error import ErrorEvent
from shared.events.job_status import JobStatusEvent
from shared.events.login import (
    CheckLoginStatusEvent,
    CredentialsLoginResultEvent,
    LoginStatusResultEvent,
    StoreLoginResult,
    TriggerAutoLoginEvent,
)


Event = Union[
    TriggerAutoLoginEvent,
    CheckLoginStatusEvent,
    LoginStatusResultEvent,
    StoreLoginResult,
    CredentialsLoginResultEvent,
    ChatMessageEvent,
    ClearChatMessagesEvent,
    DeleteClientChatsEvent,
    CredentialEntry,
    ErrorEvent,
    JobStatusEvent,
    StoreCredentialsEvent,
    DeleteClientChatsResultEvent,
    ClearChatMessagesResultEvent,
]