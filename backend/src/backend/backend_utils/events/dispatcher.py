
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage, BaseMessage

from backend.agent.history.message_adapter import to_langchain_messages
from backend.database.models.message import Message
from backend.database.engine import AsyncSessionLocal
from backend.database.repositories import (
    MessageRepository, 
    ChatRepository
)


def __normalize_content(
        content: str | list[str | dict]
    ) -> str:
    """"""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list) and content:
        first = content[0]

        if isinstance(first, str):
            return first.strip()

        if isinstance(first, dict):
            text = str(first.get("text", "")).strip()
            return text

    return ""


async def __format_message(
        message: str,
        selected_stores: list[str],
        items_per_store: int
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
        "If I am asking you to perform a search, then do it in these websites:"
        "\n"
        f"{store_list}"
        "\n"
        f"For each product, search {items_per_store} items."
    )

    return final_message


async def dispatch_chat(
        agent: Runnable,
        user_input: str,
        client_id: str,
        chat_id: str,
        selected_stores: list[str],
        items_per_store: int
    ) -> str:
    """"""

    async with AsyncSessionLocal() as db:
        previous_messages: list[Message] = (
            await MessageRepository.get_all_messages(
                db,
                client_id,
                chat_id
            )
        )

    user_message: str = await __format_message(
        user_input,
        selected_stores,
        items_per_store
    )

    lc_messages: list[BaseMessage] = to_langchain_messages(
        previous_messages
    )

    try:
        messages: dict = await agent.ainvoke(
            input={
                "messages": lc_messages + [HumanMessage(user_message)]
            },
            config={
                "configurable": {"client_id": client_id}
            }
        )

        ai_response: BaseMessage = messages["messages"][-1]

        return __normalize_content(ai_response.content)

    except Exception as e:
        return str(e)