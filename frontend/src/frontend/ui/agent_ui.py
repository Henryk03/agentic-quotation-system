
import uuid
import asyncio

import websockets
import streamlit as st
from pydantic import TypeAdapter
from websockets import ClientConnection

from frontend.frontend_utils.events.handler import handle_event

from shared.events import Event
from shared.events.chat import ChatMessageEvent
from shared.events.error import ErrorEvent
from shared.events.auth import (
    LoginRequiredEvent,
    LoginCompletedEvent,
    LoginFailedEvent,
)


# ==========================
#        Event parsing
# ==========================

event_adapter = TypeAdapter(Event)

def parse_event(raw: str) -> Event:
    return event_adapter.validate_json(raw)


# ==========================
#        Page setup
# ==========================

st.set_page_config(
    page_title="Agent Chat",
    page_icon="🤖",
    layout="centered",
)

st.title("🤖 Agent Chat")
st.caption("Streamlit chatbot powered by Google Gemini")


# ==========================
#        Session state
# ==========================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "status_placeholder" not in st.session_state:
    st.session_state.status_placeholder = st.empty()

if "ws" not in st.session_state:
    st.session_state.ws = None

if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)

if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex

if "ws_uri" not in st.session_state:
    st.session_state.ws_uri = "ws://0.0.0.0:8080/ws/chat"


# ==========================
#          Sidebar
# ==========================

with st.sidebar:
    st.header("Settings")

    st.session_state.ws_uri = st.text_input(
        "WebSocket URI",
        st.session_state.ws_uri,
    )

    st.write("Session ID:")
    st.code(st.session_state.session_id)

    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ==========================
#     Render chat history
# ==========================

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ==========================
#      WebSocket logic
# ==========================

async def ws_listener(ws: ClientConnection) -> None:
    """Ascolta continuamente eventi dal server."""

    async for raw in ws:
        try:
            event = parse_event(raw)
            handle_event(
                st.session_state.status_placeholder,
                event,
            )
        except Exception as exc:
            st.error(f"Event parse error: {exc}")


async def connect_ws() -> ClientConnection:
    """Crea connessione WS e avvia listener."""
    url = f"{st.session_state.ws_uri}?session={st.session_state.session_id}"

    for _ in range(2):
        try:
            ws = await websockets.connect(url)

            asyncio.create_task(ws_listener(ws))
            return ws
        
        except:
            asyncio.sleep(2)   


async def get_ws() -> ClientConnection:
    """"""

    ws = st.session_state.ws

    if ws is None or ws.close_code is not None:
        ws = await connect_ws()
        st.session_state.ws = ws

    return ws


async def send_text(message: str) -> None:
    """"""

    for _ in range(2):
        ws = await get_ws()

        try:
            await ws.send(message)

        except:
            st.session_state.ws = None

    raise RuntimeError("Impossibile comunicare con il server.")
        


async def send_event(event: Event) -> None:
    """"""

    for _ in range(2):
        ws = await get_ws()

        try:
            await ws.send(event.model_dump_json())

        except:
            st.session_state.ws = None

    raise RuntimeError("Impossibile comunicare con il server.")


# ==========================
#        Chat input
# ==========================

prompt: str | None = st.chat_input("Type a message...")

if prompt:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.loop.run_until_complete(
        send_text(prompt)
    )