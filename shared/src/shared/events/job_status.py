
from typing import Literal
from pydantic import BaseModel


class JobStatusEvent(BaseModel):
    """"""
    
    type: Literal["job.status"] = "job.status"
    job_id: str
    status: Literal["DONE", "FAILED", "PENDING"]