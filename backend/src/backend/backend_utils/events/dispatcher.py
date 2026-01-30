
from fastapi import WebSocket
from langchain_core.runnables import Runnable
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, BaseMessage

from backend.backend_utils.events.emitter import EventEmitter
from backend.backend_utils.exceptions import UILoginException


async def __format_message(
        message: str,
        session_id: str,
        selected_stores: list[str]
    ) -> str:
    """"""

    store_list: str

    if len(selected_stores) >= 1:
        store_list = "* " + "\n*".join(selected_stores)
    
    else:
        store_list = "* No store selected"

    final_message: str = (
        f"This is my message to you: {message}"
        "\n"
        f"This is my Session ID: {session_id}"
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
        session_id,
        selected_stores
    )

    config: RunnableConfig = {
        "configurable": {"thread_id": f"{session_id}|{chat_id}"}
    }

    try:
        messages: dict = await agent.ainvoke(
            input={"messages": [HumanMessage(user_message)]},
            config=config
        )

        ai_response: BaseMessage = messages["messages"][-1]

        await EventEmitter.emit_chat_message(
            websocket,
            ai_response,
            session_id,
            chat_id
        )

    except UILoginException as uile:
        await EventEmitter.emit_login_required(
            websocket,
            uile.provider.name,
            uile.provider.url
        )