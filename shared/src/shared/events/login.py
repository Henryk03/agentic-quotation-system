
from typing import Literal
from pydantic import BaseModel, SecretStr

# from playwright.async_api import StorageState


# class LoginRequiredEvent(BaseModel):
#     """"""

#     type: Literal["login.required"] = "login.required"
#     provider: str
#     login_url: str
#     message: str


# class AutoLoginResultEvent(BaseModel):
#     """"""

#     type: Literal[
#         "login.success",
#         "login.failed",
#         "login.cancelled",
#         "login.timeout",
#         "login.error"
#     ]
#     provider: str
#     metadata: dict
#     state: StorageState | str
#     reason: str | None = None


class CredentialEntry(BaseModel):
    """"""

    username: SecretStr
    password: SecretStr


class StoreCredentialsEvent(BaseModel):
    """"""

    type: Literal["store.credentials"] = "store.credentials"
    credentials: CredentialEntry