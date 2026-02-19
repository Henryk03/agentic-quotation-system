
from pydantic import BaseModel
from typing import Literal


class StoreLoginResult(BaseModel):
    """"""

    store: str
    success: bool
    attempts_left: int | None = None
    minutes_left: int | None = None
    error_message: str | None = None


class CredentialsLoginResultEvent(BaseModel):
    """"""

    type: Literal["credentials.login.result"] = "credentials.login.result"
    results: list[StoreLoginResult]