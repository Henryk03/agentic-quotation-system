
from typing import Literal
from pydantic import BaseModel


class CredentialEntry(BaseModel):
    """"""

    username: str
    password: str


class StoreCredentialsEvent(BaseModel):
    """"""

    type: Literal["store.credentials"] = "store.credentials"
    credentials: dict[str, CredentialEntry]