
from pydantic import BaseModel
from typing import Literal

from shared.shared_utils.common import JobStatus


class JobStatusEvent(BaseModel):
    """
    Event representing the current status of a background job.

    Attributes
    ----------
    type : Literal["job.status"]
        Discriminator identifying the event type. Always set to
        `"job.status"`.

    job_id : str
        Unique identifier of the job.

    status : JobStatus, default=JobStatus.PENDING
        Current status of the job. Can be one of `PENDING`,
        `RUNNING`, `COMPLETED`, or `FAILED`.
    
    Notes
    -----
    This event is used to track the lifecycle of a job submitted to
    the backend. It can be emitted immediately after job creation
    and updated as the job progresses or completes.
    """
    
    type: Literal["job.status"] = "job.status"
    job_id: str
    status: JobStatus = JobStatus.PENDING