
from dataclasses import dataclass


@dataclass
class LoginRequiredSignal:
    """"""

    provider: str
    reason: str = "LOGIN_REQUIRED"