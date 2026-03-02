
from pydantic import BaseModel
from typing import Literal


class CredentialEntry(BaseModel):
    """
    Model representing a single set of authentication credentials.

    Attributes
    ----------
    username : str
        Username or email associated with the store account.

    password : str
        Password associated with the store account.

    Notes
    -----
    This model is used as the value type inside the 
    `StoreCredentialsEvent.credentials` mapping. Sensitive 
    information is transported through the event system
    and should be handled securely by the backend.
    """

    username: str
    password: str


class StoreCredentialsEvent(BaseModel):
    """
    Event containing authentication credentials for one or 
    more stores.

    Attributes
    ----------
    type : Literal["store.credentials"]
        Discriminator identifying the event type. Always set to
        `"store.credentials"`.

    credentials : dict[str, CredentialEntry]
        Mapping between store identifiers and their corresponding
        credential entries.

        - Key: store name or unique store identifier.
        - Value: `CredentialEntry` containing username and password.

    Notes
    -----
    This event is typically triggered when a store requires manual
    authentication during the auto-login workflow.

    The backend is responsible for securely processing and storing
    the provided credentials if necessary.
    """

    type: Literal["store.credentials"] = "store.credentials"
    credentials: dict[str, CredentialEntry]