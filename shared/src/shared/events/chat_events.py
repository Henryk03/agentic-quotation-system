
from typing import Literal
from shared.events.base_event import BaseEvent


class AIMessageEvent(BaseEvent):
    """"""

    type: Literal["ai_message"] = "ai_message"
    content: str


class ToolMessageEvent(BaseEvent):
    """"""

    type: Literal["tool_message"] = "tool_message"
    content: str