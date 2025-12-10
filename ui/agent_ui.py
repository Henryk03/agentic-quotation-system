
import streamlit as st
import nest_asyncio
import asyncio
import websockets
from typing import Optional


nest_asyncio.apply()


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
#     Utility functions
# ==========================

async def get_ws():
    """
    Crea WS se non esiste, altrimenti riusa quello esistente.
    """

    if st.session_state.ws is None:
        st.session_state.ws = await websockets.connect(
            uri=st.session_state.ws_uri,
            ping_interval=None,
            ping_timeout=None,
            close_timeout=None
        )

    return st.session_state.ws


async def send_message(message: str) -> str:
    """
    Invia un messaggio e riceve risposta, gestendo ping/pong.
    """

    ws = await get_ws()
    await ws.send(message)

    while True:
        response = await ws.recv()

        # keep-alive from server
        if response == "__server_ping__":
            ws.send("__client_pong__")
            continue

        # server's ping response
        if response == "__server_pong__":
            continue

        return response
    

async def send_ping():
    """"""

    ws = await get_ws()

    while True:
        if ws:
            try:
                await asyncio.sleep(5)
                await ws.send("__client_ping__")
            except:
                break


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

if "ws_uri" not in st.session_state:
    st.session_state.ws_uri = "ws://agent-backend:8080/ws/chat"

if "ping_task_started" not in st.session_state:
    st.session_state.loop.create_task(send_ping())
    st.session_state.ping_task_started = True


# ==========================
#          Sidebar
# ==========================

with st.sidebar:
    st.header("Settings")

    st.session_state.ws_uri = st.text_input(
        "WebSocket URI",
        st.session_state.ws_uri
    )

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
        placeholder.markdown("Thinking…")

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