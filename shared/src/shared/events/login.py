
from pydantic import BaseModel
from typing import Literal

from shared.shared_utils.common import LoginStatus


class TriggerAutoLoginEvent(BaseModel):
    """
    Event to trigger automatic login for a specific store.

    Attributes
    ----------
    type : Literal["trigger.autologin.event"]
        Discriminator identifying the event type. Always set to
        `"trigger.autologin.event"`.

    store : str
        Identifier of the store for which auto-login should be attempted.
    """

    type: Literal["trigger.autologin.event"] = "trigger.autologin.event"
    store: str


class CheckLoginStatusEvent(BaseModel):
    """
    Event to check the current login status of a store.

    Attributes
    ----------
    type : Literal["check.login.status.event"]
        Discriminator identifying the event type. Always set to
        `"check.login.status.event"`.

    store : str
        Identifier of the store whose login status will be checked.
    """

    type: Literal["check.login.status.event"] = "check.login.status.event"
    store: str


class StoreLoginResult(BaseModel):
    """
    Result of a login attempt for a specific store.

    Attributes
    ----------
    type : Literal["store.login.result"]
        Discriminator identifying the event type. Always set to
        `"store.login.result"`.

    store : str
        Identifier of the store.

    success : bool
        Whether the login attempt was successful.

    status : LoginStatus
        Current login status of the store. Possible values are
        `VALID`, `NEEDS_CREDENTIALS`, `AUTOLOGIN_REQUIRED`, `FAILED`.

    error_message : str or None, optional
        Optional error message if the login failed. Default is None.
    """

    type: Literal["store.login.result"] = "store.login.result"
    store: str
    success: bool
    status: LoginStatus
    error_message: str | None = None


class LoginStatusResultEvent(BaseModel):
    """
    Event representing the login status result for a store.

    Attributes
    ----------
    type : Literal["login.status.result.event"]
        Discriminator identifying the event type. Always set to
        `"login.status.result.event"`.

    result : StoreLoginResult
        Result object containing the status and details of the store login.
    """

    type: Literal["login.status.result.event"] = "login.status.result.event"
    result: StoreLoginResult


class CredentialsLoginResultEvent(BaseModel):
    """
    Event representing the result of credential-based login attempts
    for one or more stores.

    Attributes
    ----------
    type : Literal["credentials.login.result"]
        Discriminator identifying the event type. Always set to
        `"credentials.login.result"`.

    results : list of StoreLoginResult
        List of login results for each store attempted with provided 
        credentials.
    """

    type: Literal["credentials.login.result"] = "credentials.login.result"
    results: list[StoreLoginResult]