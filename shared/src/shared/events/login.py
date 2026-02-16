
from typing import Literal
from pydantic import BaseModel

from playwright.async_api import StorageState


class LoginRequiredEvent(BaseModel):
    """"""

    type: Literal["login.required"] = "login.required"
    provider: str
    login_url: str
    message: str


class LoginResultEvent(BaseModel):
    """"""

    type: Literal[
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

    type: Literal[
        "autologin.credentials.provided", 
        "autologin.credentials.received"
    ]
    credentials: dict[str, dict[str, str]] | None