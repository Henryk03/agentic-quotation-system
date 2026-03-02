
import time
from typing import Any

import requests
from requests import Response
from pydantic import TypeAdapter

from shared.events import Event, ErrorEvent
from shared.events.transport import EventEnvelope


class RESTClient:
    """
    HTTP client responsible for sending events to the backend and
    retrieving their asynchronous results.

    Notes
    -----
    This client communicates with the backend using a job-based pattern:

    1. An event is submitted via POST.
    2. A `job_id` is returned.
    3. The job status is polled until completion or failure.
    4. The final result is deserialized into an `Event` instance.

    Event deserialization is performed using a Pydantic `TypeAdapter`.
    """


    __event_adapter: TypeAdapter = TypeAdapter(Event) 


    def __init__(
            self,
            base_url: str,
            client_id: str
        ) -> None:
        """
        Initialize the REST client.

        Parameters
        ----------
        base_url : str
            Base URL of the backend service (e.g., `http://localhost:8000`).
            Trailing slashes are automatically removed.

        client_id : str
            Unique identifier associated with the client instance.

        Returns
        -------
        None
        """

        self.base_url = base_url.rstrip("/")
        self.client_id = client_id


    def send_event(
            self,
            event: Event
        ) -> str | None:
        """
        Send an event to the backend for asynchronous processing.

        Parameters
        ----------
        event : Event
            The event instance to be sent.

        Returns
        -------
        str or None
            The job identifier assigned by the backend if the request is
            successful, otherwise `None`.

        Raises
        ------
        requests.HTTPError
            If the HTTP request fails.

        Notes
        -----
        The event is wrapped inside an `EventEnvelope` containing the
        client identifier before being serialized and sent.
        """

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
        """
        Retrieve the status and result of a previously submitted job.

        Parameters
        ----------
        event_id : str
            The identifier of the job returned by `send_event`.

        Returns
        -------
        dict[str, Any]
            A dictionary containing the job status and, if available,
            the result payload.

        Raises
        ------
        requests.HTTPError
            If the HTTP request fails.
        """

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
        """
        Send an event and block until the corresponding 
        job completes.

        Parameters
        ----------
        event : Event
            The event to be sent to the backend.

        poll_interval : float, default=0.5
            Time interval (in seconds) between successive 
            polling attempts.

        timeout : float, default=120.0
            Maximum time (in seconds) to wait for job completion.

        Returns
        -------
        Event
            The resulting event returned by the backend. If 
            deserialization fails or the backend reports an 
            error, an `ErrorEvent` is returned.

        Raises
        ------
        RuntimeError
            If no job identifier is returned after submitting the event.

        TimeoutError
            If the job does not complete within the specified timeout.

        requests.HTTPError
            If any HTTP request fails.

        Notes
        -----
        The method implements a polling mechanism:

        - Submits the event.
        - Periodically checks job status.
        - Deserializes the result into an `Event` instance using a
        Pydantic `TypeAdapter`.
        - Returns an `ErrorEvent` if validation fails.
        """
        
        event_id: str | None = self.send_event(event)

        if not event_id:
            raise RuntimeError(
                f"Backend did not return a job_id for event of type "
                f"{type(event).__name__}."
            )
        
        deadline: float = time.time() + timeout

        while time.time() < deadline:
            job_data: dict[str, Any] = self.get_job(event_id)
            status: str = job_data.get("status", "FAILED")

            if status in ("COMPLETED", "FAILED"):
                result_data: dict[str, Any] = job_data.get(
                    "result", 
                    {}
                )

                try:
                    return self.__event_adapter.validate_python(
                        result_data
                    )
                
                except Exception as e:
                    error_msg: str = job_data.get("error") or str(e)
                    return ErrorEvent(
                        message = error_msg,
                        metadata = (
                            getattr(event, "metadata", None) 
                            or 
                            None
                        )
                    )
                
            time.sleep(poll_interval)
            
        raise TimeoutError(f"Timeout waiting for job {event_id}")