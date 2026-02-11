
from sqlalchemy.ext.asyncio import AsyncSession

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
from shared.events.error import ErrorEvent
from shared.events.login import AutoLoginCredentialsEvent


class EventHandler:
    """"""


    @staticmethod
    async def __ensure_client(
            db: AsyncSession,
            session_id: str
        ) -> Client:
        """"""

        return await client_repo.get_or_create_client(
            db,
            session_id
        )
    

    @staticmethod
    async def __ensure_chat(
            db: AsyncSession,
            chat_id: str,
            session_id: str
        ) -> Chat:
        """"""

        return await chat_repo.get_or_create_chat(
            db,
            chat_id,
            session_id
        )


    @staticmethod
    async def handle_event(
            db: AsyncSession,
            event: Event,
            session_id: str,
            websocket: WebSocket
        ) -> None:
        """"""

        event_type: str = getattr(event, "event", "error")

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
            
            case "login.success":
                return await EventHandler.__handle_browser_context(
                    db, 
                    event, 
                    session_id, 
                    websocket
                )

            case "login.failed":
                return await EventHandler.__handle_login_failed(
                    db,
                    event,
                    session_id,
                    websocket
                )

            case "login.error":
                return await EventHandler.__handle_login_failed(
                    db,
                    event,
                    session_id,
                    websocket
                )

            case "login.cancelled":
                return await EventHandler.__handle_login_cancelled(
                    db,
                    event,
                    session_id,
                    websocket
                )
            
            case "chat.clear_messages":
                return await EventHandler.__handle_clear_messages(
                    db,
                    event,
                    session_id,
                    websocket
                )
            
            case "client.clear_chats":
                return await EventHandler.__handle_delete_chats(
                    db,
                    session_id,
                    websocket
                )

            case _:
                pass


    @staticmethod
    async def __handle_credentials(
            db: AsyncSession, 
            event: Event, 
            session_id: str,
            websocket: WebSocket
        ) -> None:
        """"""

        for store, creds in event.credentials.items():
            await credential_repo.upsert_credentials(
                db, 
                session_id, 
                store, 
                creds["username"], 
                creds["password"]
            )

        await EventEmitter.emit_event(
            websocket,
            AutoLoginCredentialsEvent(
                event="autologin.credentials.received",
                credentials=None
            )
        )


    @staticmethod
    async def __handle_chat_message(
            db: AsyncSession,
            event: Event,
            session_id: str,
            websocket: WebSocket
        ) -> None:
        """"""

        role: str = event.role
        message: str = event.content

        chat_id: str = event.metadata.get("chat_id")
        selected_stores: list[str] = event.metadata.get("selected_stores")
        custom_stores: list[str] = event.metadata.get("custom_urls")
        items_per_store: int = event.metadata.get("items_per_store")

        all_selected_stores: list[str] = selected_stores + custom_stores

        _ = await EventHandler.__ensure_chat(db, chat_id, session_id)

        await message_repo.save_message(
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
                all_selected_stores,
                items_per_store,
                websocket
            )

    
    @staticmethod
    async def __handle_browser_context(
            db: AsyncSession,
            event: Event, 
            session_id: str,
            websocket: WebSocket
        ) -> None:
        """"""
        
        chat_id: str = event.metadata.get("chat_id")
        selected_stores: list[str] = event.metadata.get("selected_stores")
    
        await browser_context_repo.add_login_attempt(
            db,
            session_id,
            event.provider,
            "success",
            None
        )

        await browser_context_repo.upsert_browser_context(
            db,
            session_id,
            event.provider,
            event.state,
            None
        )

        last_message = await message_repo.get_last_user_message(
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
    async def __handle_login_failed(
            db: AsyncSession,
            event: Event,
            session_id: str,
            websocket: WebSocket
        ) -> None:
        """"""

        chat_id: str = event.metadata.get("chat_id")
        selected_stores: list[str] = event.metadata.get("selected_stores")
        fail_reason: str | None = event.reason

        await browser_context_repo.add_login_attempt(
            db,
            session_id,
            event.provider,
            "failed",
            fail_reason
        )

        can_retry, block_reason = await browser_context_repo.can_attempt_login(
            db,
            session_id,
            event.provider
        )

        if not can_retry:
            await browser_context_repo.upsert_browser_context(
                db,
                session_id,
                event.provider,
                "BLOCKED",
                block_reason
            )

            if selected_stores and len(selected_stores) > 0:
                last_message = await message_repo.get_last_user_message(
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

            else:
                await EventEmitter.emit_event(
                    websocket,
                    ErrorEvent(
                        message="No providers available. All login attemps failed."
                    )
                )

        else:
            last_message = await message_repo.get_last_user_message(
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
    async def __handle_login_cancelled(
            db: AsyncSession,
            event: Event,
            session_id: str,
            websocket: WebSocket
        ) -> None:
        """"""

        chat_id: str = event.metadata.get("chat_id")
        selected_stores: list[str] = event.metadata.get("selected_stores", [])

        await browser_context_repo.add_login_attempt(
            db, 
            session_id, 
            event.provider,
            status="cancelled", 
            reason="User cancelled"
        )

        if event.provider in selected_stores:
            selected_stores.remove(event.provider)
        
        if selected_stores:
            last_message = await message_repo.get_last_user_message(
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

        else:
            await EventEmitter.emit_event(
                websocket,
                ErrorEvent(
                    message="All providers cancelled"
                )
            )


    @staticmethod
    async def __handle_clear_messages(
            db: AsyncSession,
            event: Event,
            session_id: str,
            websocket: WebSocket
        ) -> None:
        """"""

        chat_id: str = event.chat_id

        try:
            await message_repo.delete_messages_for_chat(
                db,
                session_id,
                chat_id,
            )

        except Exception as e:
            await EventEmitter.emit_event(
                websocket,
                ErrorEvent(
                    message=str(e)
                )
            )


    @staticmethod
    async def __handle_delete_chats(
            db: AsyncSession,
            session_id: str,
            websocket: WebSocket
        ) -> None:
        """"""

        try:
            await chat_repo.delete_all_chats_for_client(
                db,
                session_id
            )

        except Exception as e:
            print(str(e))
            await EventEmitter.emit_event(
                websocket,
                ErrorEvent(
                    message=str(e)
                )
            )