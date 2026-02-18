
from typing import Literal
from pydantic import BaseModel

from shared.shared_utils.common import JobStatus


class JobStatusEvent(BaseModel):
    """"""
    
    type: Literal["job.status"] = "job.status"
    job_id: str
    status: JobStatus = JobStatus.PENDING