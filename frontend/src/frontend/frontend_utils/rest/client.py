
import time
import asyncio
import logging
import requests
from pydantic import TypeAdapter
from typing import Any
from requests import Response
from asyncio import AbstractEventLoop

from shared.events import Event
from shared.events import ErrorEvent
from shared.events.transport import EventEnvelope


class RESTClient:
    """"""


    __event_adapter: TypeAdapter = TypeAdapter(Event) 


    def __init__(
            self,
            base_url: str,
            client_id: str
        ) -> None:
        """"""

        self.base_url = base_url.rstrip("/")
        self.client_id = client_id


    def send_event(
            self,
            event: Event
        ) -> str | None:
        """"""

        envelope: EventEnvelope = EventEnvelope(
            client_id = self.client_id,
            event = event
        )

        response: Response = requests.post(
            url = f"{self.base_url}/event",
            json = envelope.model_dump(
                serialize_as_any = True, 
                mode = "json"
            )
        )

        response.raise_for_status()

        job_data: dict[str, Any] = response.json()

        return job_data.get("job_id")
    

    def get_job(
            self,
            event_id: str
        ) -> dict[str, Any]:
        """"""

        response: Response = requests.get(
            url = f"{self.base_url}/event/{event_id}"
        )

        response.raise_for_status()

        return response.json()
    

    def send_and_wait(
            self,
            event: Event,
            poll_interval: float = 0.5,
            timeout: float = 120.0
        ) -> Event:
        """"""
        event_id: str | None = self.send_event(event)

        if not event_id:
            raise RuntimeError("...")
        
        deadline: float = time.time() + timeout

        while time.time() < deadline:
            job_data: dict[str, Any] = self.get_job(event_id)
            status: str = job_data.get("status", "FAILED")

            if status in ("COMPLETED", "FAILED"):
                result_data: dict[str, Any] = job_data.get("result", {})

                try:
                    return self.__event_adapter.validate_python(result_data)
                
                except Exception as e:
                    error_msg: str = job_data.get("error") or str(e)
                    return ErrorEvent(
                        message=error_msg,
                        metadata=getattr(event, "metadata", None) or None
                    )
                
            time.sleep(poll_interval)
            
        raise TimeoutError(f"Timeout waiting for job {event_id}")