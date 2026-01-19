
from fastapi import WebSocket
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
    SystemMessage,
    BaseMessage
)

from backend.database.engine import SessionLocal
from backend.database.repositories import message_repo

from shared.events.chat import ChatMessageEvent
from shared.events.error import ErrorEvent
from shared.events.auth import (
    LoginRequiredEvent,
    LoginCompletedEvent,
    LoginFailedEvent,
)


def langchain_message_to_event(message: BaseMessage) -> ChatMessageEvent | None:
    """Converte un messaggio LangChain in un ChatMessageEvent."""

    if isinstance(message, AIMessage):
        role = "assistant"
        content = message.content

        if isinstance(content, list):
            tmp_content = content[0]["text"]
            content = tmp_content

    elif isinstance(message, HumanMessage):
        role = "user"
        content = message.content

    elif isinstance(message, ToolMessage):
        role = "tool"
        content = message.content

    elif isinstance(message, SystemMessage):
        return  # no event will be emitted with system messages

    else:
        raise TypeError(f"Unsupported LangChain message: {type(message)}")

    return ChatMessageEvent(
        role=role,
        content=content
    )


async def emit_message(
        websocket: WebSocket,
        message: BaseMessage,
        session_id: str,
        chat_id: str
    ) -> None:
    """"""

    try:
        event = langchain_message_to_event(message)

        if not event:
            return 
        
        with SessionLocal() as db:
            message_repo.save_message(
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


async def emit_login_completed(
        websocket: WebSocket,
        provider: str
    ) -> None:
    """"""

    event = LoginCompletedEvent(provider=provider)
    await websocket.send_text(event.model_dump_json())


async def emit_login_failed(
        websocket: WebSocket,
        provider: str,
        reason: str | None = None
    ) -> None:
    """"""

    event = LoginFailedEvent(provider=provider, reason=reason)
    await websocket.send_text(event.model_dump_json())