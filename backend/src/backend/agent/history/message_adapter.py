
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    BaseMessage,
)

from backend.database.models.message import Message


def to_langchain_messages(
        messages: list[Message],
    ) -> list[BaseMessage]:
    """"""

    langchain_messages: list[BaseMessage] = []

    for msg in messages:
        match msg.role:
            case "user":
                langchain_messages.append(HumanMessage(content=msg.content))

            case "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
                
            case _:
                continue

    return langchain_messages