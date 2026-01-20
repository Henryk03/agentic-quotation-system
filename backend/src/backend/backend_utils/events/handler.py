
from sqlalchemy.orm import Session

from fastapi import WebSocket

from backend.database.repositories import (
    client_repo,
    chat_repo,
    message_repo,
    credential_repo,
    browser_context_repo
)

from shared.events import Event


class EventHandler:
    """"""

    @staticmethod
    async def handle_event(
            db: Session,
            event: Event,
            session_id: str,
            websocket: WebSocket
        ) -> None:
        """"""

        event_type = getattr(event, "event", None)

        if event_type == "autologin.credentials.provided":
            return await EventHandler.__handle_credentials(db, event, session_id)
        
        elif event_type == "chat.message":
            return await EventHandler.__handle_chat_message(db, event, session_id)
        
        # Aggiungi altri casi qui...

    @staticmethod
    async def __handle_credentials(db: Session, event, session_id: str):
        # Sposta qui la logica degli upsert
        for store, creds in event.credentials.items():
            credential_repo.upsert_credentials(
                db, session_id, store, creds["username"], creds["password"]
            )
        db.commit()

    @staticmethod
    async def __handle_chat_message(db: Session, event, session_id: str):
        # Sposta qui la logica di creazione chat e salvataggio messaggi
        pass