
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


async def __format_message(
        message: str,
        selected_stores: list[str]
    ) -> str:
    """"""

    if len(selected_stores) >= 1:
        store_list = "* " + "\n*".join(selected_stores)
    
    else:
        store_list = "* No store selected"

    final_message: str = (
        "This is my message to you:"
        "\n"
        f"{message}"
        "\n"
        "If I am asking you to perform a search, then do it in these websites:"
        "\n"
        f"{store_list}"
    )

    return final_message


async def dispatch_chat(
        agent: Runnable,
        user_input: str,
        session_id: str,
        chat_id: str,
        selected_stores: list[str],
        websocket: WebSocket,
    ) -> None:
    """"""

    user_message: str = await __format_message(
        user_input,
        selected_stores
    )

    try:
        async for state in agent.astream(
                input={"messages": [HumanMessage(user_message)]},
                config={"thread_id": chat_id},
                stream_mode="updates"
            ):

            for _, data in state.items():
                message = data["messages"][-1]
                is_tool_call = message.content.strip() == ""

                if is_tool_call:
                    continue

                await emit_message(
                    websocket,
                    message,
                    session_id,
                    chat_id
                )

    except ManualFallbackException as mfe:
        await emit_login_required(
            websocket,
            provider=mfe.name,
            login_url=mfe.url
        )

        try:
            # waiting a login-related event from the UI
            await wait_for_login(websocket)

            # ...

        except Exception as login_exc:
            # ...
            pass