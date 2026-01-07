
from typing import Literal
from utils.events.base_event import BaseEvent


class LoginRequiredEvent(BaseEvent):
    """"""

    type: Literal["login_required"] = "login_required"
    provider: str
    login_url: str
    reason: str | None = None


class LoginCompletedEvent(BaseEvent):
    """"""

    type: Literal["login_completed"] = "login_completed"
    provider: str