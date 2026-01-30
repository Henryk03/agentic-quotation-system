
from typing import Literal

from fastapi import WebSocket
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
    SystemMessage,
    BaseMessage
)

from backend.database.engine import AsyncSessionLocal
from backend.database.repositories import message_repo

from shared.events import Event
from shared.events.chat import ChatMessageEvent
from shared.events.error import ErrorEvent
from shared.events.login import LoginRequiredEvent


class EventEmitter:
    """"""


    @staticmethod
    def __get_langchain_role(
            message: BaseMessage
        ) -> Literal["assistant", "tool", "user", "system"] | None:
        """"""

        match message:
            case AIMessage():
                return "assistant"
            
            case ToolMessage():
                return "tool"
            
            case HumanMessage():
                return "user"
            
            case SystemMessage():
                return "system"
            
            case _:
                return None
            

    @staticmethod
    def __normalize_content(
            content: str | list[str | dict]
        ) -> str | None:
        """"""

        if isinstance(content, str):
            return content.strip() or None

        if isinstance(content, list) and content:
            first = content[0]

            if isinstance(first, str):
                return first.strip() or None

            if isinstance(first, dict):
                text = str(first.get("text", "")).strip()
                return text or None

        return None


    @staticmethod
    def __langchain_message_to_event(
            message: BaseMessage
        ) -> ChatMessageEvent | None:
        """"""

        role: str | None = EventEmitter.__get_langchain_role(
            message
        )

        if role != "assistant":
            return None
        
        content: str | None = EventEmitter.__normalize_content(
            message.content
        )

        if not content:
            return None

        return ChatMessageEvent(
            role=role,
            content=content
        )


    @staticmethod
    async def emit_chat_message(
            websocket: WebSocket,
            message: BaseMessage,
            session_id: str,
            chat_id: str
        ) -> None:
        """"""

        try:
            event: Event | None = EventEmitter.__langchain_message_to_event(
                message
            )

            if not event:
                return None
            
            async with AsyncSessionLocal() as db:
                await message_repo.save_message(
                    db,
                    session_id,
                    chat_id,
                    event.role,
                    event.content
                )

            await websocket.send_text(event.model_dump_json())

        except Exception as e:
            err = ErrorEvent(message=str(e))
            await websocket.send_text(err.model_dump_json())


    @staticmethod
    async def emit_event(
            websocket: WebSocket,
            event: Event
        ) -> None:
        """"""

        await websocket.send_text(event.model_dump_json())


    @staticmethod
    async def emit_login_required(
            websocket: WebSocket,
            provider: str,
            login_url: str
        ) -> None:
        """"""

        event = LoginRequiredEvent(
            provider=provider,
            login_url=login_url,
            message="È richiesto il login manuale per continuare"
        )
        await websocket.send_text(event.model_dump_json())


    # @staticmethod
    # async def emit_login_completed(
    #         websocket: WebSocket,
    #         provider: str
    #     ) -> None:
    #     """"""

    #     event = LoginCompletedEvent(provider=provider)
    #     await websocket.send_text(event.model_dump_json())


    # @staticmethod
    # async def emit_login_failed(
    #         websocket: WebSocket,
    #         provider: str,
    #         reason: str | None = None
    #     ) -> None:
    #     """"""

    #     event = LoginFailedEvent(provider=provider, reason=reason)
    #     await websocket.send_text(event.model_dump_json())