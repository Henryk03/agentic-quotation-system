
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.agent.main_agent import graph as agent
from backend.backend_utils.events.emitter import EventEmitter
from backend.backend_utils.events.dispatcher import dispatch_chat
from backend.database.models.chat import Chat
from backend.database.models.client import Client
from backend.database.repositories import (
    ClientRepository,
    ChatRepository,
    CredentialsRepository,
    BrowserContextRepository,
    MessageRepository
)

from shared.events import Event
from shared.events.error import ErrorEvent
from shared.events.chat import ChatMessageEvent
from shared.events.login import AutoLoginCredentialsEvent


class EventHandler:
    """"""


    @staticmethod
    async def __ensure_client(
            db: AsyncSession,
            session_id: str
        ) -> Client:
        """"""

        return await ClientRepository.get_or_create_client(
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

        return await ChatRepository.get_or_create_chat(
            db,
            chat_id,
            session_id
        )


    @staticmethod
    async def handle_event(
            db: AsyncSession,
            event: Event,
            session_id: str
        ) -> dict:
        """"""

        event_type: str = getattr(event, "type")

        _ = await EventHandler.__ensure_client(db, session_id)

        match event_type:
            case "autologin.credentials.provided":
                return await EventHandler.__handle_credentials(
                    db, 
                    event, 
                    session_id
                )
            
            case "chat.message":
                return await EventHandler.__handle_chat_message(
                    db, 
                    event, 
                    session_id
                )
            
            # case "login.success":
            #     return await EventHandler.__handle_browser_context(
            #         db, 
            #         event, 
            #         session_id
            #     )

            # case "login.failed":
            #     return await EventHandler.__handle_login_failed(
            #         db,
            #         event,
            #         session_id
            #     )

            # case "login.error":
            #     return await EventHandler.__handle_login_failed(
            #         db,
            #         event,
            #         session_id
            #     )

            # case "login.cancelled":
            #     return await EventHandler.__handle_login_cancelled(
            #         db,
            #         event,
            #         session_id
            #     )
            
            case "chat.clear_messages":
                return await EventHandler.__handle_clear_messages(
                    db,
                    event,
                    session_id
                )
            
            case "client.clear_chats":
                return await EventHandler.__handle_delete_chats(
                    db,
                    session_id
                )

            case _:
                pass


    @staticmethod
    async def __handle_credentials(
            db: AsyncSession, 
            event: Event, 
            session_id: str
        ) -> dict:
        """"""

        if settings.AUTO_LOGIN_ONLY:
            are_valid_credentials: bool = False

        for store, creds in event.credentials.items():
            await CredentialsRepository.upsert_credentials(
                db, 
                session_id, 
                store, 
                creds["username"], 
                creds["password"]
            )

        result_event: Event = AutoLoginCredentialsEvent(
            event="autologin.credentials.received",
            credentials=None
        )

        return result_event.model_dump()


    @staticmethod
    async def __handle_chat_message(
            db: AsyncSession,
            event: Event,
            session_id: str
        ) -> dict:
        """"""

        ai_response: str | None = None

        role: str = event.role
        message: str = event.content

        chat_id: str = event.metadata.get("chat_id")
        selected_stores: list[str] = event.metadata.get("selected_stores")
        custom_stores: list[str] = event.metadata.get("custom_urls")
        items_per_store: int = event.metadata.get("items_per_store")

        all_selected_stores: list[str] = selected_stores + custom_stores

        _ = await EventHandler.__ensure_chat(db, chat_id, session_id)

        await MessageRepository.save_message(
            db,
            session_id,
            chat_id,
            role,
            message
        )

        if role == "user":
            ai_response = await dispatch_chat(
                agent,
                message,
                session_id,
                chat_id,
                all_selected_stores,
                items_per_store
            )

        result_event: Event = ChatMessageEvent(
            role = "assistant",
            content = ai_response,
            metadata = event.metadata
        )

        return result_event.model_dump()

    
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
            session_id: str
        ) -> dict:
        """"""

        chat_id: str = event.chat_id

        try:
            await MessageRepository.delete_messages_for_chat(
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
            session_id: str
        ) -> None:
        """"""

        try:
            await ChatMessageEvent.delete_all_chats_for_client(
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