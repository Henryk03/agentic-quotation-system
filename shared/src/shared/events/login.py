
from pydantic import BaseModel, model_validator
from typing import Literal

from shared.shared_utils.common import LoginStatus


class TriggerAutoLoginEvent(BaseModel):
    """"""

    store: str


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

    @model_validator(mode = "after")
    def validate_invariants(self):
        """"""

        if self.status == LoginStatus.COOLDOWN:
            if self.minutes_left is None:
                raise ValueError(
                    "COOLDOWN status requires minutes_left"
                )

        if self.status == LoginStatus.FAILED:
            if self.attempts_left is None:
                raise ValueError(
                    "FAILED status requires attempts_left"
                )

        return self


class LoginStatusResultEvent(BaseModel):
    """"""

    result: StoreLoginResult


class CredentialsLoginResultEvent(BaseModel):
    """"""

    type: Literal["credentials.login.result"] = "credentials.login.result"
    results: list[StoreLoginResult]