
from datetime import datetime, timezone
from playwright.async_api import StorageState
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from backend.agent.main_agent import graph as agent
from backend.backend_utils.browser.login_service import validate_credentials
from backend.backend_utils.events.dispatcher import dispatch_chat
from backend.database.models.chat import Chat
from backend.database.models.client import Client
from backend.database.repositories import (
    ChatRepository,
    ClientRepository,
    CredentialsRepository,
    LoginContextRepository,
    MessageRepository,
)

from shared.events import Event
from shared.events.chat import ChatMessageEvent
from shared.events.clear import ClearChatMessagesEvent, ClearClientChatsEvent
from shared.events.credentials import StoreCredentialsEvent
from shared.events.login import CredentialsLoginResultEvent, StoreLoginResult
from shared.events.metadata import StoreMetadata


class EventHandler:
    """"""


    @staticmethod
    async def __ensure_client(
            db: AsyncSession,
            client_id: str
        ) -> Client:
        """"""

        return await ClientRepository.get_or_create_client(
            db,
            client_id
        )
    

    @staticmethod
    async def __ensure_chat(
            db: AsyncSession,
            chat_id: str,
            client_id: str
        ) -> Chat:
        """"""

        return await ChatRepository.get_or_create_chat(
            db,
            chat_id,
            client_id
        )


    @staticmethod
    async def handle_event(
            db: AsyncSession,
            event: Event,
            client_id: str
        ) -> dict:
        """"""

        _ = await EventHandler.__ensure_client(db, client_id)

        match event:
            case StoreCredentialsEvent():
                return await EventHandler.__handle_credentials(
                    db, 
                    event, 
                    client_id
                )
            
            case ChatMessageEvent():
                return await EventHandler.__handle_chat_message(
                    db, 
                    event, 
                    client_id
                )
            
            # case ClearChatMessagesEvent():
            #     pass
            
            # case ClearClientChatsEvent():
            #     pass

            case _:
                raise Exception("Event not supported.")


    @staticmethod
    async def __handle_credentials(
            db: AsyncSession, 
            event: StoreCredentialsEvent, 
            client_id: str
        ) -> dict:
        """"""

        results: list[StoreLoginResult] = []

        for store, entry in event.credentials.items():
            context = await LoginContextRepository.get_or_create_context(
                db,
                client_id,
                store
            )

            attempts_left: int | None = None
            minutes_left: int | None = None

            now: datetime = datetime.now(timezone.utc)

            if context.locked_until and context.locked_until > now:
                minutes_left = int(
                    ((context.locked_until - now).total_seconds() + 59) // 60
                )

                results.append(
                    StoreLoginResult(
                        store = store,
                        success = False,
                        attempts_left = 0,
                        minutes_left = minutes_left,
                        error_message = context.last_error_message
                    )
                )

                continue

            if context.locked_until and context.locked_until <= now:
                context.locked_until = None
                context.current_attemps = 0

            success: bool = False
            storage_state: StorageState | None = None
            error_message: str | None = None

            try:
                success, storage_state, error_message = (
                    await validate_credentials(
                        store = store,
                        username = entry.username.get_secret_value(),
                        password = entry.password.get_secret_value()
                    )
                )

            except Exception as e:
                success = False
                storage_state = None
                error_message = str(e)

            await LoginContextRepository.add_login_attempt(
                db,
                client_id,
                store,
                success,
                reason = None if success else error_message
            )

            if context.locked_until and context.locked_until > now:
                attempts_left = 0
                minutes_left = int(
                    ((context.locked_until - now).total_seconds() + 59) // 60
                )

            else:
                attempts_left = (
                    context.max_attempts - context.current_attemps
                )

            if success:
                await CredentialsRepository.upsert_credentials(
                    db,
                    client_id,
                    store,
                    entry.username.get_secret_value(),
                    entry.password.get_secret_value()
                )

                if storage_state:
                    await LoginContextRepository.upsert_context(
                        db,
                        client_id,
                        store,
                        storage_state
                    )

                results.append(
                    StoreLoginResult(
                        store = store,
                        success = True,
                        attempts_left = attempts_left
                    )
                )

            else:

                results.append(
                    StoreLoginResult(
                        store = store,
                        success = False,
                        attempts_left = attempts_left,
                        minutes_left = minutes_left,
                        error_message = error_message
                    )
                )

        result_event = CredentialsLoginResultEvent(
            results=results
        )

        return result_event.model_dump()


    @staticmethod
    async def __handle_chat_message(
            db: AsyncSession,
            event: ChatMessageEvent,
            client_id: str
        ) -> dict:
        """"""

        ai_response: str | None = None

        role: str = event.role
        message: str = event.content
        metadata: StoreMetadata | None = event.metadata

        if not metadata:
            raise ValueError("Metadata missing.")
        
        chat_id: str = getattr(metadata, "chat_id")
        selected_stores: list[str] = getattr(metadata, "selected_stores")
        custom_stores: list[str] = getattr(metadata, "custom_store_urls")
        items_per_store: int = getattr(metadata, "items_per_store")

        all_selected_stores: list[str] = selected_stores + custom_stores

        _ = await EventHandler.__ensure_chat(db, chat_id, client_id)

        await MessageRepository.save_message(
            db,
            client_id,
            chat_id,
            role,
            message
        )

        ai_response = await dispatch_chat(
            agent,
            message,
            client_id,
            chat_id,
            all_selected_stores,
            items_per_store
        )

        result_event: Event = ChatMessageEvent(
            role = "assistant",
            content = ai_response,
            metadata = None
        )

        return result_event.model_dump()


    # @staticmethod
    # async def __handle_clear_messages(
    #         db: AsyncSession,
    #         event: Event,
    #         client_id: str
    #     ) -> dict:
    #     """"""

    #     chat_id: str = event.chat_id

    #     try:
    #         await MessageRepository.delete_messages_for_chat(
    #             db,
    #             client_id,
    #             chat_id,
    #         )

    #     except Exception as e:
    #         await EventEmitter.emit_event(
    #             websocket,
    #             ErrorEvent(
    #                 message=str(e)
    #             )
    #         )


    # @staticmethod
    # async def __handle_delete_chats(
    #         db: AsyncSession,
    #         client_id: str
    #     ) -> None:
    #     """"""

    #     try:
    #         await ChatMessageEvent.delete_all_chats_for_client(
    #             db,
    #             client_id
    #         )

    #     except Exception as e:
    #         print(str(e))
    #         await EventEmitter.emit_event(
    #             websocket,
    #             ErrorEvent(
    #                 message=str(e)
    #             )
    #         )