
from fastapi import WebSocket
from src.main_agent import run_agent
from langchain.messages import AIMessage, ToolMessage
from utils.common.exceptions import ManualFallbackException, LoginFailedException
from utils.events import AIMessageEvent, ToolMessageEvent, ErrorEvent, LoginRequiredEvent


async def run_agent_with_events(
        message: str,
        session_id: str,
        websocket: WebSocket
    ) -> None:
    """"""

    try:
        result = await run_agent(message, session_id)
        result_content = result.content

        # could happen that the received message is inside
        # a list containing a dict with the response text
        if isinstance(result_content, list):
            result_content = result_content[0].get("text")

        if isinstance(result, AIMessage):
            event = AIMessageEvent(content=result_content)
        elif isinstance(result, ToolMessage):
            event = ToolMessageEvent(content=result_content)
            
    except ManualFallbackException as mfe:
        event = LoginRequiredEvent(
            provider=mfe.provider.name,
            login_url=mfe.provider.url
        )

    except Exception as e:
        event = ErrorEvent(
            message=str(e)
        )

    finally:
        await websocket.send_text(event.to_json_str())