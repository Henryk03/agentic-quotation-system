
import asyncio
import logging
import requests
from pydantic import TypeAdapter
from typing import Any
from requests import Response
from asyncio import AbstractEventLoop

from shared.events import Event
from shared.events.transport import EventEnvelope


__event_adapter: TypeAdapter = TypeAdapter(Event)


class RESTClient:
    """"""    


    def __init__(
            self,
            base_url: str,
            session_id: str
        ) -> None:
        """"""

        self.base_url = base_url.rstrip("/")
        self.session_id = session_id


    def send_event(
            self,
            event: Event
        ) -> str | None:
        """"""

        envelope: EventEnvelope = EventEnvelope(
            session_id = self.session_id,
            event = event
        )

        response: Response = requests.post(
            url = self.base_url,
            json = envelope.model_dump()
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
    

    async def send_and_wait(
            self,
            event: Event,
            poll_interval: float = 0.5,
            timeout: float = 60.0
        ) -> Event:
        """"""

        event_id: str | None = self.send_event(event)

        loop: AbstractEventLoop = asyncio.get_event_loop()
        deadline: float = loop.time() + timeout

        if event_id:
            while loop.time() < deadline:
                job_data: dict[str, Any] = self.get_job(event_id)

                status: str = job_data.get("status", "FAILED")

                if status == "COMPLETED":
                    result_data: dict[str, Any] = job_data.get("result", {})

                    return __event_adapter.validate_python(result_data)
                
                if status == "FAILED":
                    raise Exception(
                        job_data.get("error", "Something went wrong.")
                    )
                
                await asyncio.sleep(poll_interval)

        raise TimeoutError(f"Timeout waiting for job {event_id}")