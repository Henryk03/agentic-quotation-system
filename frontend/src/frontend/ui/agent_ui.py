
import time
import uuid
import asyncio
import websockets
import streamlit as st
from typing import Optional
from shared.events import Event
from pydantic import TypeAdapter
from websockets import ClientConnection
from playwright.sync_api import sync_playwright
from streamlit.delta_generator import DeltaGenerator


event_adapter = TypeAdapter(Event)

LOGIN_COUNTDOWN_MESSAGE: str = (
    "**Accesso richiesto**\n\n"
    "Per continuare è necessario continuare il login manualmente.\n\n"
    "Tra 5 secondi si aprirà automaticamente una nuova scheda "
    "del browser in cui potrai effettuare il login in modo sicuro.\n\n"
    "Dopo aver effettuato il login, torna qui: il processo riprenderà "
    "automaticamente."
)


# ==========================
#    Page setup and title
# ==========================

st.set_page_config(
    page_title="Agent Chat",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Agent Chat")
st.caption("Streamlit chatbot powered by Google Gemini")


# ==========================
#       Session state
# ==========================

# chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# temporary placeholder for status events
if "status_placeholder" not in st.session_state:
    st.session_state.status_placeholder = st.empty()

# websocket connection
if "ws" not in st.session_state:
    st.session_state.ws = None

# asyncio loop to execute async functions
if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)

# chat session id
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4().hex)

# websocket server uri
if "ws_uri" not in st.session_state:
    st.session_state.ws_uri = "ws://0.0.0.0:8080/ws/chat"


# ==========================
#          Sidebar
# ==========================

with st.sidebar:
    st.header("Settings")

    st.session_state.ws_uri = st.text_input(
        "WebSocket URI",
        st.session_state.ws_uri
    )

    st.write("Session ID:", st.session_state.session_id)

    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ==========================
#    Render chat history
# ==========================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ==========================
#     Utility functions
# ==========================

def parse_events(raw_event: str) -> Event:
    """"""

    return event_adapter.validate_json(raw_event)


def handle_event(
        placeholder: DeltaGenerator,
        event: Event
    ) -> None:
    """"""

    match event.type:
        case "ai_message":
            placeholder.markdown(event.content)

            st.session_state.messages.append({
                "role": "assistant",
                "content": event.content
            })

        case "tool_message":
            with st.chat_message("tool"):
                st.markdown(event.content)

            st.session_state.messages.append({
                "role": "tool",
                "content": event.content
            })

        case "login_required":
            st.session_state.loop.run_until_complete(
                animated_countdown(
                    seconds=5,
                    message_format=LOGIN_COUNTDOWN_MESSAGE,
                    placeholder=placeholder
                )
            )
            
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=False, channel="chrome")
                page = browser.new_page()

                page.goto(event.login_url)

                time.sleep(10)


        case "login_completed":
            placeholder.success(
                "✅ Login completato con successo. "
                "Sto riprendendo l'operazione..."
            )

        case "error":
            st.error(event.message)

        case _:
            pass


async def animated_countdown(
        seconds: int,
        message_format: str,
        placeholder: DeltaGenerator
    ) -> None:
    """"""

    with st.chat_message("assistant"):
        for remaining in range(seconds, 0, -1):
            placeholder.warning(
                message_format.format(remaining)
            )
            await asyncio.sleep(1)

    placeholder.empty()


async def connect_ws() -> ClientConnection:
    """Connette la WebSocket con retry."""

    url = f"{st.session_state.ws_uri}?session={st.session_state.session_id}"

    for _ in range(2):
        try:
            ws = await websockets.connect(url)
            return ws
        
        except:
            await asyncio.sleep(2)


async def get_ws() -> ClientConnection:
    """Ritorna una WS attiva, altrimenti la ricrea."""

    ws = st.session_state.ws

    if ws is None or ws.close_code is not None:
        ws = await connect_ws()
        st.session_state.ws = ws

    return ws


async def send_message(message: str) -> Event:
    """Invia un messaggio con retry automatico."""

    for _ in range(2):
        ws = await get_ws()

        try:
            await ws.send(message)
            response = await ws.recv()
            
            return parse_events(response)
        
        except:
            st.session_state.ws = None
            await asyncio.sleep(0.5)

    raise RuntimeError("Impossibile comunicare con il server.")


# ==========================
#        Chat input
# ==========================

prompt: Optional[str] = st.chat_input(
    placeholder="Type a message..."
)

if prompt:
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Thinking...")

        try:
            answer_event = st.session_state.loop.run_until_complete(
                send_message(prompt)
            )

            handle_event(placeholder, answer_event)

        except Exception as e:
            err = f"WebSocket Error: {e}"
            placeholder.error(err)

            st.session_state.messages.append(
                {"role": "assistant", "content": f"⚠️ {err}"}
            )