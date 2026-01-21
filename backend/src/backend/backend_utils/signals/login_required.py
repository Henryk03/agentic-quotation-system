
from dataclasses import dataclass


@dataclass
class LoginRequiredSignal:
    """"""

    provider: str
    login_url: str
    reason: str = "LOGIN_REQUIRED"