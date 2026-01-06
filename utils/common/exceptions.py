
from utils.provider.base_provider import BaseProvider


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

    def __init__(self, provider: BaseProvider):
        self.provider = provider
        super().__init__(
            (
                f"Login failed while logging into '{provider.name}'. "
                "Please try again."
            )
        )


class ManualFallbackException(Exception):
    """
    Exception raised when the automatic login procedure fails and
    a manual login is required in order to continue the workflow.

    Attributes:
        provider (BaseProvider):
            The provider for which the login failed.

        message (str | None):
            Optional custom error message.
    """

    def __init__(
            self,
            provider: BaseProvider,
            message: str | None = None
        ):
        self.provider = provider

        default_message = (
            f"Auto-login failed while logging into '{provider.name}'. "
            "Proceeding with manual login."
        )

        super().__init__(message or default_message)
