
from enum import Enum


class JobStatus(str, Enum):
    """
    Enum representing the execution status of a job.

    Attributes
    ----------
    PENDING : str
        The job has been created but not yet started.

    RUNNING : str
        The job is currently in progress.

    COMPLETED : str
        The job has finished successfully.

    FAILED : str
        The job has finished with an error.
    """
    
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class LoginStatus(str, Enum):
    """
    Enum representing the authentication status of a store 
    login attempt.

    Attributes
    ----------
    VALID : str
        The login credentials are valid and authentication 
        succeeded.

    FAILED : str
        The login attempt failed due to invalid credentials 
        or other errors.

    NEEDS_CREDENTIALS : str
        The store requires the user to input credentials 
        manually.

    AUTOLOGIN_REQUIRED : str
        Automatic login must be attempted (credentials 
        already stored).
    """

    VALID = "valid"
    FAILED = "failed"
    NEEDS_CREDENTIALS = "needs_credentials"
    AUTOLOGIN_REQUIRED = "autologin_required"