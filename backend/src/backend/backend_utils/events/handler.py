
from datetime import datetime, timezone
from playwright.async_api import StorageState
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from backend.agent.main_agent import graph as agent
from backend.backend_utils.browser.login_service import (
    validate_state,
    validate_credentials,
    execute_autologin
)
from backend.backend_utils.events.dispatcher import dispatch_chat
from backend.database.models.chat import Chat
from backend.database.models.client import Client
from backend.database.models.login_context import LoginContext
from backend.database.repositories import (
    ChatRepository,
    ClientRepository,
    CredentialsRepository,
    LoginContextRepository,
    MessageRepository,
)

from shared.events import Event
from shared.events.chat import ChatMessageEvent
from shared.events.clear import (
    ClearChatMessagesResultEvent, 
    ClearChatMessagesEvent, 
    DeleteClientChatsResultEvent,
    DeleteClientChatsEvent
)
from shared.events.credentials import StoreCredentialsEvent
from shared.events.login import (
    CredentialsLoginResultEvent, 
    StoreLoginResult,
    CheckLoginStatusEvent,
    LoginStatusResultEvent,
    TriggerAutoLoginEvent,
)
from shared.events.metadata import StoreMetadata, BaseMetadata
from shared.shared_utils.common import LoginStatus


class EventHandler:
    """"""


    @staticmethod
    async def __ensure_client(
            db: AsyncSession,
            client_id: str
        ) -> Client:
        """"""

        client: Client = await ClientRepository.get_or_create_client(
            db,
            client_id
        )
        await db.commit()

        return client
    

    @staticmethod
    async def __ensure_chat(
            db: AsyncSession,
            chat_id: str,
            client_id: str
        ) -> Chat:
        """"""

        chat: Chat = await ChatRepository.get_or_create_chat(
            db,
            chat_id,
            client_id
        )
        await db.commit()

        return chat


    @staticmethod
    async def __get_current_status(
            db: AsyncSession,
            client_id: str,
            store: str,
            force_validate_state: bool = True
        ) -> tuple[LoginStatus, int | None, int | None, str | None]:
        """"""

        context: LoginContext = (
            await LoginContextRepository.get_or_create_context(
                db, 
                client_id, 
                store
            )
        )

        now: datetime = datetime.now(timezone.utc)

        if context.locked_until:
            if context.locked_until > now:
                minutes_left: int = int(
                    ((context.locked_until - now).total_seconds() + 59) // 60
                )

                return (
                    LoginStatus.COOLDOWN,
                    0,
                    minutes_left,
                    context.last_error_message,
                )

            context.locked_until = None
            context.current_attempts = 0

            await db.flush()

        attempts_left: int = context.max_attempts - context.current_attempts

        if context.context_data and force_validate_state:
            state: StorageState | None = (
                await LoginContextRepository.get_storage_state(
                    db, 
                    client_id, 
                    store
                )
            )

            if state:
                try:
                    if await validate_state(store, state):
                        return (
                            LoginStatus.VALID, 
                            attempts_left, 
                            None, 
                            None
                        )
                    
                    else:
                        return (
                            LoginStatus.AUTOLOGIN_REQUIRED, 
                            attempts_left, 
                            None, 
                            "Session expired"
                        )
                    
                except:
                    return (
                        LoginStatus.AUTOLOGIN_REQUIRED, 
                        attempts_left, 
                        None, 
                        "Session validation failed"
                    )
                
        username: str | None
        password: str | None

        username, password = (
            await CredentialsRepository.get_credentials(
                db, 
                client_id, 
                store
            )
        )

        if username and password:
            return (
                LoginStatus.AUTOLOGIN_REQUIRED, 
                attempts_left, 
                None, 
                None
            )

        return (
            LoginStatus.NEEDS_CREDENTIALS, 
            attempts_left, 
            None, 
            "No credentials provided"
        )


    @staticmethod
    async def handle_event(
            db: AsyncSession,
            event: Event,
            client_id: str
        ) -> dict[str, Any]:
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
            
            case ClearChatMessagesEvent():
                return await EventHandler.__handle_clear_messages(
                    db,
                    event,
                    client_id
                )
            
            case DeleteClientChatsEvent():
                return await EventHandler.__handle_delete_chats(
                    db,
                    client_id
                )
            
            case CheckLoginStatusEvent():
                return await EventHandler.__handle_check_status(
                    db,
                    event,
                    client_id
                )
            
            case TriggerAutoLoginEvent():
                return await EventHandler.__handle_autologin(
                    db,
                    event,
                    client_id
                )

            case _:
                raise Exception("Event not supported.")


    @staticmethod
    async def __handle_credentials(
            db: AsyncSession,
            event: StoreCredentialsEvent,
            client_id: str,
        ) -> dict:
        """"""

        results: list[StoreLoginResult] = []

        for store, entry in event.credentials.items():
            now: datetime = datetime.now(timezone.utc)

            context: LoginContext = (
                await LoginContextRepository.get_or_create_context(
                    db, 
                    client_id, 
                    store
                )
            )

            if context.locked_until and context.locked_until > now:
                minutes_left = int(
                    ((context.locked_until - now).total_seconds() + 59) // 60
                )

                results.append(
                    StoreLoginResult(
                        store = store,
                        success = False,
                        status = LoginStatus.COOLDOWN,
                        attempts_left = 0,
                        minutes_left = minutes_left,
                        error_message = context.last_error_message,
                    )
                )

                continue

            success: bool = False
            storage_state: StorageState | None = None
            error_message: str | None = None

            try:
                success, storage_state, error_message = (
                    await validate_credentials(
                        store = store,
                        username = entry.username,
                        password = entry.password,
                    )
                )

            except Exception as e:
                success = False
                error_message = str(e)

            context = await LoginContextRepository.add_login_attempt(
                db, 
                context, 
                success, 
                reason = None if success else error_message
            )

            now = datetime.now(timezone.utc)

            if context.locked_until and context.locked_until > now:
                minutes_left = int(
                    ((context.locked_until - now).total_seconds() + 59) // 60
                )

                results.append(
                    StoreLoginResult(
                        store = store,
                        success = False,
                        status = LoginStatus.COOLDOWN,
                        attempts_left = 0,
                        minutes_left = minutes_left,
                        error_message = context.last_error_message,
                    )
                )

                continue

            if success:
                await CredentialsRepository.upsert_credentials(
                    db, 
                    client_id, 
                    store, 
                    username = entry.username, 
                    password = entry.password
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
                        status = LoginStatus.VALID
                    )
                )

                continue

            attempts_left = context.max_attempts - context.current_attempts

            results.append(
                StoreLoginResult(
                    store = store,
                    success = False,
                    status = LoginStatus.FAILED,
                    attempts_left = attempts_left,
                    minutes_left = None,
                    error_message = error_message,
                )
            )

        return CredentialsLoginResultEvent(
            results = results
        ).model_dump()


    @staticmethod
    async def __handle_chat_message(
            db: AsyncSession,
            event: ChatMessageEvent,
            client_id: str
        ) -> dict[str, Any]:
        """"""

        ai_response: str | None = None

        role: str = event.role
        message: str = event.content
        metadata: StoreMetadata | None = event.metadata

        if not metadata:
            raise ValueError("Metadata missing.")
        
        chat_id: str = getattr(metadata, "chat_id")
        selected_stores: list[str] = getattr(metadata, "selected_stores")
        custom_stores: list[str] = getattr(metadata, "selected_external_store_urls")
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

        await MessageRepository.save_message(
            db,
            client_id,
            chat_id,
            role = "assistant",
            content = ai_response
        )

        result_event: Event = ChatMessageEvent(
            role = "assistant",
            content = ai_response,
            metadata = None
        )

        return result_event.model_dump()


    @staticmethod
    async def __handle_clear_messages(
            db: AsyncSession,
            event: ClearChatMessagesEvent,
            client_id: str
        ) -> dict[str, Any]:
        """"""

        metadata: BaseMetadata = event.metadata
        chat_id: str = getattr(metadata, "chat_id")

        success: bool = False

        try:
            await MessageRepository.delete_messages_for_chat(
                db,
                client_id,
                chat_id,
            )

            success = True

        except:
            pass

        result_event: Event = ClearChatMessagesResultEvent(
            metadata = metadata,
            success = success
        )

        return result_event.model_dump()


    @staticmethod
    async def __handle_delete_chats(
            db: AsyncSession,
            client_id: str
        ) -> dict[str, Any]:
        """"""

        success: bool = False

        try:
            await ChatRepository.delete_all_chats_for_client(
                db,
                client_id
            )

            success = True

        except:
            pass

        result_event: Event = DeleteClientChatsResultEvent(
            success = success
        )

        return result_event.model_dump()
    

    @staticmethod
    async def __handle_check_status(
            db: AsyncSession,
            event: CheckLoginStatusEvent,
            client_id: str,
        ) -> dict[str, Any]:
        """"""

        store: str = event.store

        status: LoginStatus
        attempts_left: int | None
        minutes_left: int | None
        error_message: str | None

        status, attempts_left, minutes_left, error_message = (
            await EventHandler.__get_current_status(
                db, 
                client_id, 
                store, 
                force_validate_state = True
            )
        )

        return LoginStatusResultEvent(
            result = StoreLoginResult(
                store = store,
                success = (status == LoginStatus.VALID),
                status = status,
                attempts_left = attempts_left,
                minutes_left = minutes_left,
                error_message = error_message,
            )
        ).model_dump()
    

    @staticmethod
    async def __handle_autologin(
            db: AsyncSession,
            event: TriggerAutoLoginEvent,
            client_id: str,
        ) -> dict[str, Any]:
        """"""

        store: str = event.store

        status: LoginStatus
        attempts_left: int | None
        minutes_left: int | None
        error_message: str | None

        status, attempts_left, minutes_left, error_message = (
            await EventHandler.__get_current_status(
                db, 
                client_id, 
                store, 
                force_validate_state = True
            )
        )

        if status != LoginStatus.AUTOLOGIN_REQUIRED:
            return LoginStatusResultEvent(
                result = StoreLoginResult(
                    store = store,
                    success = (status == LoginStatus.VALID),
                    status = status,
                    attempts_left = attempts_left,
                    minutes_left = minutes_left,
                    error_message = error_message
                )
            ).model_dump()

        username: str | None = None
        password: str | None = None

        username, password = (
            await CredentialsRepository.get_credentials(
                db, 
                client_id, 
                store
            )
        )

        success: bool = False
        storage_state: StorageState | None = None

        try:
            if username and password:
                success, storage_state = await execute_autologin(
                    store, 
                    username, 
                    password
                )

        except Exception:
            success = False
            storage_state = None

        if success:
            if storage_state:
                await LoginContextRepository.upsert_context(
                    db,
                    client_id,
                    store,
                    storage_state
                )

            status = LoginStatus.VALID

        else:
            status = LoginStatus.FAILED

        return LoginStatusResultEvent(
            result = StoreLoginResult(
                store = store,
                success = (status == LoginStatus.VALID),
                status = status,
            )
        ).model_dump()