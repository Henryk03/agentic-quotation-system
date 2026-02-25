
from pydantic import BaseModel
from typing import Literal

from shared.shared_utils.common import LoginStatus


class TriggerAutoLoginEvent(BaseModel):
    """"""

    type: Literal["trigger.autologin.event"] = "trigger.autologin.event"
    store: str


class CheckLoginStatusEvent(BaseModel):
    """"""

    type: Literal["check.login.status.event"] = "check.login.status.event"
    store: str


class StoreLoginResult(BaseModel):
    """"""

    type: Literal["store.login.result"] = "store.login.result"
    store: str
    success: bool
    status: LoginStatus
    error_message: str | None = None


class LoginStatusResultEvent(BaseModel):
    """"""

    type: Literal["login.status.result.event"] = "login.status.result.event"
    result: StoreLoginResult


class CredentialsLoginResultEvent(BaseModel):
    """"""

    type: Literal["credentials.login.result"] = "credentials.login.result"
    results: list[StoreLoginResult]