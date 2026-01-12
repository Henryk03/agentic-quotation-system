
from backend.provider.base_provider import BaseProvider


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
