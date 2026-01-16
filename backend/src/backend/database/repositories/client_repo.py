
from sqlalchemy.orm import Session

from backend.database.models.client import Client


def get_or_create_client(
        db: Session,
        session_id: str
    ) -> Client:
    """"""

    client = db.get(Client, session_id)

    if not client:
        client = Client(session_id=session_id)
        
        db.add(client)
        db.commit()

    return client