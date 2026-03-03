
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
)

from backend.database.models.message import Message


def to_langchain_messages(
        messages: list[Message],
    ) -> list[BaseMessage]:
    """
    Convert database Message objects into LangChain message objects.

    Parameters
    ----------
    messages : list[Message]
        List of database message instances containing at least
        a `role` and `content` field.

    Returns
    -------
    list[BaseMessage]
        A list of LangChain-compatible message objects.
        - Messages with role "user" are converted to `HumanMessage`.
        - Messages with role "assistant" are converted to `AIMessage`.
        - Any other role is ignored.
    """

    langchain_messages: list[BaseMessage] = []

    for msg in messages:
        match msg.role:
            case "user":
                langchain_messages.append(
                    HumanMessage(content = msg.content)
                )

            case "assistant":
                langchain_messages.append(
                    AIMessage(content=msg.content)
                )
                
            case _:
                continue

    return langchain_messages