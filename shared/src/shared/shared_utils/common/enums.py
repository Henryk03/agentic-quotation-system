
from enum import Enum


class JobStatus(str, Enum):
    """"""
    
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class LoginStatus(str, Enum):
    """"""

    VALID = "valid"
    COOLDOWN = "cooldown"
    NEEDS_CREDENTIALS = "needs_credentials"
    AUTOLOGIN_REQUIRED = "autologin_required"