
import asyncio

from fastapi import WebSocket
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage

from backend.backend_utils.events.login_waiter import wait_for_login
from backend.backend_utils.exceptions import (
    LoginFailedException,
    ManualFallbackException
)
from backend.backend_utils.events.emitter import (
    emit_message, 
    emit_login_required,
    emit_login_completed,
    emit_login_failed
)


async def dispatch_chat(
        agent: Runnable,
        user_input: str,
        session_id: str,
        metadata: dict[str, list[str]],
        websocket: WebSocket,
    ) -> None:
    """
    Gestisce una richiesta chat:
    - invia input a LangChain
    - streamma gli eventi verso il client
    """

    # capire come trasportare i metadati alla funzione di ricerca prodotti

    try:
        async for state in agent.astream(
                input={"messages": [HumanMessage(user_input)]},
                config={"thread_id": session_id},
                stream_mode="updates"
            ):

            for _, data in state.items():
                message = data["messages"][-1]
                await emit_message(websocket, message=message)

    except ManualFallbackException as mfe:
        await emit_login_required(
            websocket,
            provider=mfe.name,
            login_url=mfe.url
        )

        try:
            # waiting a login-related event from the UI
            await wait_for_login(websocket)

            await emit_login_completed(
                websocket,
                provider=mfe.name
            )

        except Exception as login_exc:
            await emit_login_failed(
                websocket,
                provider=mfe.name,
                reason=str(login_exc)
            )