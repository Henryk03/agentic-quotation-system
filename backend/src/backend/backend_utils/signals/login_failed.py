
from dataclasses import dataclass


@dataclass
class LoginFailedSignal:
    """"""

    provider: str
    reason: str = "LOGIN_FAILED"