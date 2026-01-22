
import asyncio

from fastapi import WebSocket
from langchain_core.runnables import Runnable
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, BaseMessage

from backend.backend_utils.events.emitter import EventEmitter
from backend.backend_utils.signals.login_required import LoginRequiredSignal


async def __format_message(
        message: str,
        selected_stores: list[str]
    ) -> str:
    """"""

    store_list: str

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

    config: RunnableConfig = {
        "configurable": {"thread_id": chat_id}
    }

    try:
        async for state in agent.astream(
                input={"messages": [HumanMessage(user_message)]},
                config=config,
                stream_mode="updates"
            ):

            for _, data in state.items():
                message_or_signal: BaseMessage | LoginRequiredSignal = (
                    data["messages"][-1]
                )

                if isinstance(message_or_signal, LoginRequiredSignal):
                    signal: LoginRequiredSignal = message_or_signal

                    await EventEmitter.emit_login_required(
                        websocket,
                        signal.provider,
                        signal.login_url
                    )

                elif isinstance(message_or_signal, BaseMessage):
                    message: BaseMessage = message_or_signal

                    await EventEmitter.emit_chat_message(
                        websocket,
                        message,
                        session_id,
                        chat_id
                    )
                
    except Exception as e:
        pass                    # decidere cosa fare...