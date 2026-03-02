
from langchain_core.runnables import Runnable
from langchain_core.messages import BaseMessage, HumanMessage

from backend.agent.history.message_adapter import to_langchain_messages
from backend.database.engine import AsyncSessionLocal
from backend.database.models.message import Message
from backend.database.repositories import MessageRepository


def __normalize_content(
        content: str | list[str | dict]
    ) -> str:
    """
    Normalize various content formats into a single string.

    Parameters
    ----------
    content : str or list of str or dict
        The message content, which may be a simple string, 
        a list of strings, or a list of dictionaries containing 
        a 'text' key.

    Returns
    -------
    str
        The normalized text content with leading and trailing 
        whitespace removed. Returns an empty string if content 
        is empty or unrecognized.
    """

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


async def dispatch_chat(
        agent: Runnable,
        user_input: str,
        client_id: str,
        chat_id: str,
        selected_stores: list[str],
        items_per_store: int
    ) -> str:
    """
    Send a user message to the agent and retrieve the 
    AI response.

    This function fetches previous messages from the 
    database, converts them to LangChain messages, 
    invokes the agent with the current user input, and
    normalizes the returned response content.

    Parameters
    ----------
    agent : Runnable
        The LangChain agent to invoke.

    user_input : str
        The text input from the user.

    client_id : str
        Identifier for the client using the system.

    chat_id : str
        Identifier for the specific chat session.

    selected_stores : list of str
        Stores selected for scraping or querying.

    items_per_store : int
        Number of items to query per store.

    Returns
    -------
    str
        Normalized text content returned by the agent. 
        If an exception occurs, the error message string 
        is returned instead.
    """

    async with AsyncSessionLocal() as db:
        previous_messages: list[Message] = (
            await MessageRepository.get_all_messages(
                db,
                client_id,
                chat_id
            )
        )

    lc_messages: list[BaseMessage] = to_langchain_messages(
        previous_messages
    )

    try:
        messages: dict = await agent.ainvoke(
            input = {
                "messages": lc_messages + [HumanMessage(user_input)]
            },
            config = {
                "configurable": {
                    "client_id": client_id,
                    "selected_stores": selected_stores,
                    "items_per_store": items_per_store
                }
            }
        )

        ai_response: BaseMessage = messages["messages"][-1]

        return __normalize_content(ai_response.content)

    except Exception as e:
        return str(e)