
from typing import Literal
from pydantic import BaseModel


class LoginRequiredEvent(BaseModel):
    """"""

    event: Literal["login.required"] = "login.required"
    provider: str
    login_url: str
    message: str


class LoginCompletedEvent(BaseModel):
    """"""

    event: Literal["login.completed"] = "login.completed"
    provider: str
    message: str


class LoginFailedEvent(BaseModel):
    """"""

    event: Literal["login.failed"] = "login.failed"
    provider: str
    reason: str | None = None