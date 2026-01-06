
import streamlit as st
import asyncio
import websockets
import uuid
from typing import Optional
from websockets import ClientConnection


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

if "messages" not in st.session_state:
    st.session_state.messages = []

if "ws" not in st.session_state:
    st.session_state.ws = None

if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(st.session_state.loop)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4().hex)

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


async def send_message(message: str) -> str:
    """Invia un messaggio con retry automatico."""

    for _ in range(2):
        ws = await get_ws()

        try:
            await ws.send(message)
            response = await ws.recv()
            return response

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
            answer = st.session_state.loop.run_until_complete(
                send_message(prompt)
            )

            placeholder.markdown(answer)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )

        except Exception as e:
            err = f"WebSocket Error: {e}"
            placeholder.error(err)

            st.session_state.messages.append(
                {"role": "assistant", "content": f"⚠️ {err}"}
            )