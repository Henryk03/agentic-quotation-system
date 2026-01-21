
from shared.provider.base_provider import BaseProvider


class LoginFailedException(Exception):
    """
    Exception raised when the login procedure for a provider
    cannot be completed successfully.

    This exception indicates that all login attempts have failed,
    and the caller should either retry the operation or switch
    to a fallback mechanism if available.

    Attributes:
        provider (BaseProvider):
            The provider for which the login failed.
    """


    def __init__(
            self,
            provider: BaseProvider,
            reason: str | None = None
        ):

        self.provider = provider
        self.reason = reason

        base_message = f"Login failed while logging into {provider.name}."

        if reason:
            full_message = f"{base_message} Reason: {reason}."

        else:
            full_message = f"{base_message} Please try again."

        super().__init__(full_message)