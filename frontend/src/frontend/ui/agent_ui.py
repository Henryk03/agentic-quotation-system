
import uuid
import asyncio
import logging

import websockets
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from pydantic import TypeAdapter
from websockets import ClientConnection

from frontend.frontend_utils.browser import *
from frontend.frontend_utils.websocket.client import WSClient
from frontend.frontend_utils.websocket.protocol import receive_events

from shared.events import Event
from shared.events.chat import ChatMessageEvent
from shared.events.error import ErrorEvent
from shared.events.auth import (
    LoginRequiredEvent,
    LoginCompletedEvent,
    LoginFailedEvent,
)


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

if "ui_state" not in st.session_state:
    st.session_state.ui_state = {
        "login_in_progress": False,
        "login_message": None,
        "login_url": None,

        "sidebar_visible": True,

        "selected_stores": ["Comet", "GruppoComet"],

        "chats": {
            "default": st.session_state.messages
        },

        "current_chat": "default",
    }

if "ws_client" not in st.session_state:
    st.session_state.ws_client = WSClient(
        websocket=None,
        session_id=uuid.uuid4().hex,
        websocket_uri="websocket://0.0.0.0:8080/websocket/chat"
    )

    logging.basicConfig(
        level=logging.INFO,
        format=""
    )


# ==========================
#          Helpers
# ==========================

def get_event_loop() -> asyncio.AbstractEventLoop:
    """"""

    if "loop" not in st.session_state:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        st.session_state.loop = loop

    return st.session_state.loop



# ==========================
#      Event handling
# ==========================

def handle_event(
        event: Event,
        placeholder: DeltaGenerator | None = None,
    ) -> bool:
    """"""

    # ==========================
    #  Chat messages (persist)
    # ==========================
    if isinstance(event, ChatMessageEvent):
        st.session_state.ui_state["login_in_progress"] = False
        st.session_state.ui_state["login_message"] = None
        st.session_state.ui_state["login_url"] = None

        # tool calls will be ignored
        content = event.content

        if isinstance(content, list):
            content = content[0].get("text")

        st.session_state.messages.append(
            {
                "role": event.role,
                "content": content,
            }
        )

        return True

    # ==========================
    #      Errors (persist)
    # ==========================
    if isinstance(event, ErrorEvent):
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"⚠️ {event.message}",
            }
        )

        return True
    
    # ==========================
    #   Login flow (temporary)
    # ==========================
    if isinstance(event, LoginRequiredEvent):
        st.session_state.ui_state["login_in_progress"] = True
        st.session_state.ui_state["login_message"] = event.message
        st.session_state.ui_state["login_url"] = str(event.login_url)
        
        return False

    if isinstance(event, LoginCompletedEvent):
        st.session_state.ui_state["login_in_progress"] = False
        st.session_state.ui_state["login_message"] = None
        st.session_state.ui_state["login_url"] = None

        return False

    if isinstance(event, LoginFailedEvent):
        st.session_state.ui_state["login_in_progress"] = False
        st.session_state.ui_state["login_message"] = None
        st.session_state.ui_state["login_url"] = None
        
        return False


def on_event(event: Event) -> None:
    """"""

    handle_event(
        event,
        st.session_state.status_placeholder
    )


def on_error(exception: Exception) -> None:
    """"""

    pass


# ==========================
#      Header controls
# ==========================

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("📁 Sidebar"):
        st.session_state.ui_state["sidebar_visible"] = (
            not st.session_state.ui_state["sidebar_visible"]
        )

with col2:
    if st.button("\u2795 Nuova Chat"):
        chat_id = uuid.uuid4().hex

        st.session_state.ui_state["chats"][chat_id] = []
        st.session_state.ui_state["current_chat"] = chat_id
        st.session_state.messages = []

        st.rerun()

with col3:
    st.session_state.ui_state["selected_stores"] = st.multiselect(
        "Store",
        options=["Comet", "GruppoComet"],
        default=st.session_state.ui_state["selected_stores"],
        label_visibility="collapsed",
    )


# ==========================
#          Sidebar
# ==========================

if st.session_state.ui_state["sidebar_visible"]:
    with st.sidebar:
        st.header("Chat")

        for chat_id in st.session_state.ui_state["chats"]:
            if st.button(f"💬 {chat_id}", key=f"chat-{chat_id}"):
                st.session_state.ui_state["current_chat"] = chat_id
                st.session_state.messages = (
                    st.session_state.ui_state["chats"][chat_id]
                )
                st.rerun()

        st.divider()

        if st.button("🧹 Clear chat"):
            st.session_state.messages = []
            st.rerun()


# ==========================
#    Render chat history
# ==========================

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


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

    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                metadata = {
                    "selected_stores": st.session_state.ui_state["selected_store"]
                }

                received_events = get_event_loop().run_until_complete(
                    st.session_state.ws_client.send(
                        prompt,
                        metadata,
                        on_event,
                        on_error
                    )
                )
        
        if received_events:
            st.rerun()
        
    except Exception as e:
        err = f"WebSocket Error: {e}"

        st.session_state.messages.append(
            {"role": "assistant", "content": f"⚠️ {err}"}
        )