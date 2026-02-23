
from pydantic import BaseModel
from typing import Literal

from shared.shared_utils.common import LoginStatus


class CheckLoginStatusEvent(BaseModel):
    """"""

    store: str


class StoreLoginResult(BaseModel):
    """"""

    store: str
    success: bool
    status: LoginStatus
    attempts_left: int | None = None
    minutes_left: int | None = None
    error_message: str | None = None


class LoginStatusResultEvent(BaseModel):
    """"""

    result: StoreLoginResult


class CredentialsLoginResultEvent(BaseModel):
    """"""

    type: Literal["credentials.login.result"] = "credentials.login.result"
    results: list[StoreLoginResult]