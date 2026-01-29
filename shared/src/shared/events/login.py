
from typing import Literal
from pydantic import BaseModel

from playwright.async_api import StorageState


class LoginRequiredEvent(BaseModel):
    """"""

    event: Literal["login.required"] = "login.required"
    provider: str
    login_url: str
    message: str


class LoginResultEvent(BaseModel):
    """"""

    event: Literal[
        "login.success",
        "login.failed",
        "login.cancelled",
        "login.timeout",
        "login.error"
    ]
    provider: str
    metadata: dict
    state: StorageState | str
    reason: str | None = None


class AutoLoginCredentialsEvent(BaseModel):
    """"""

    event: Literal[
        "autologin.credential.provided", 
        "autologin.credentials.received"
    ]
    credentials: dict | None