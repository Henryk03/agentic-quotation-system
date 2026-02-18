
from typing import Union

from shared.events.chat import ChatMessageEvent
from shared.events.clear import ClearChatMessagesEvent, ClearClientChatsEvent
from shared.events.credentials import CredentialEntry, StoreCredentialsEvent
from shared.events.error import ErrorEvent
from shared.events.job_status import JobStatusEvent


Event = Union[
    ChatMessageEvent,
    ClearChatMessagesEvent,
    ClearClientChatsEvent,
    CredentialEntry,
    ErrorEvent,
    JobStatusEvent,
    StoreCredentialsEvent
]