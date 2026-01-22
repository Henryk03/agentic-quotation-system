
from sqlalchemy.orm import Session
from typing import Literal

from fastapi import WebSocket

from backend.agent.main_agent import graph as agent
from backend.backend_utils.events.emitter import EventEmitter
from backend.backend_utils.events.dispatcher import dispatch_chat
from backend.database.models.chat import Chat
from backend.database.models.client import Client
from backend.database.repositories import (
    client_repo,
    chat_repo,
    message_repo,
    credential_repo,
    browser_context_repo
)

from shared.events import Event
from shared.events.auth import AutoLoginCredentialsEvent


class EventHandler:
    """"""


    @staticmethod
    async def __ensure_client(
            db: Session,
            session_id: str
        ) -> Client:
        """"""

        return client_repo.get_or_create_client(
            db,
            session_id
        )
    

    @staticmethod
    async def __ensure_chat(
            db: Session,
            chat_id: str,
            session_id: str
        ) -> Chat:
        """"""

        return chat_repo.get_or_create_chat(
            db,
            chat_id,
            session_id
        )


    @staticmethod
    async def handle_event(
            db: Session,
            event: Event,
            session_id: str,
            websocket: WebSocket
        ) -> None:
        """"""

        event_type: Literal[
            "autologin.credentials.provided",
            "chat.message",
            "login.completed",
            "login.failed",
            "error"
        ] = getattr(event, "event", "error")

        _ = await EventHandler.__ensure_client(db, session_id)

        match event_type:
            case "autologin.credentials.provided":
                return await EventHandler.__handle_credentials(
                    db, 
                    event, 
                    session_id, 
                    websocket
                )
            
            case "chat.message":
                return await EventHandler.__handle_chat_message(
                    db, 
                    event, 
                    session_id, 
                    websocket
                )
            
            case "login.completed":
                return await EventHandler.__handle_browser_context(
                    db, 
                    event, 
                    session_id, 
                    websocket
                )

            case "login.failed":
                return await EventHandler.__handle_failed_login(
                    db,
                    event,
                    session_id,
                    websocket
                )

            case "error":
                pass

            case _:
                pass


    @staticmethod
    async def __handle_credentials(
            db: Session, 
            event: Event, 
            session_id: str,
            websocket: WebSocket
        ) -> None:
        """"""

        if event.event != "autologin.credential.provided":
            return None

        for store, creds in event.credentials.items():
            credential_repo.upsert_credentials(
                db, session_id, store, creds["username"], creds["password"]
            )

        await EventEmitter.emit_event(
            websocket,
            AutoLoginCredentialsEvent(
                event="autologin.credentials.received",
                provider=event.provider,
                credentials=None
            )
        )


    @staticmethod
    async def __handle_chat_message(
            db: Session,
            event: Event,
            session_id: str,
            websocket: WebSocket
        ) -> None:
        """"""

        if event.event != "chat.message":
            return None

        role = event.role
        message = event.message

        chat_id = event.metadata.get("chat_id")
        selected_stores = event.metadata.get("selected_stores")

        _ = await EventHandler.__ensure_chat(db, chat_id, session_id)

        message_repo.save_message(
            db,
            session_id,
            chat_id,
            role,
            message
        )

        if role == "user":
            await dispatch_chat(
                agent,
                message,
                session_id,
                chat_id,
                selected_stores,
                websocket
            )

    
    @staticmethod
    async def __handle_browser_context(
            db: Session,
            event: Event, 
            session_id: str,
            websocket: WebSocket
        ) -> None:
        """"""

        if event.event != "login.completed":
            return None
        
        chat_id: str = event.metadata.get("chat_id")
        selected_stores: list[str] = event.metadata.get("selected_stores")
    
        browser_context_repo.upsert_browser_context(
            db,
            session_id,
            event.store,
            event.state,
            None
        )

        last_message = message_repo.get_last_user_message(
            db, 
            session_id, 
            chat_id
        )

        if last_message:
            await dispatch_chat(
                agent,
                last_message,
                session_id,
                chat_id,
                selected_stores,
                websocket
            )


    @staticmethod
    async def __handle_failed_login(
            db: Session,
            event: Event,
            session_id: str,
            websocket: WebSocket
        ) -> None:
        """"""

        if event.event != "login.failed":
            return None

        chat_id: str = event.metadata.get("chat_id")
        selected_stores: list[str] = event.metadata.get("selected_stores")
        fail_reason: str | None = event.reason

        if event.state == "LOGIN_FAILED":
            browser_context_repo.upsert_browser_context(
                db,
                session_id,
                event.provider,
                event.state,
                fail_reason
            )

        last_message = message_repo.get_last_user_message(
            db, 
            session_id, 
            chat_id
        )

        if last_message:
            await dispatch_chat(
                agent,
                last_message,
                session_id,
                chat_id,
                selected_stores,
                websocket
            )