
import uuid
import asyncio
import logging

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from frontend.frontend_utils.browser import *
from frontend.frontend_utils.websocket.client import WSClient

from shared.provider.registry import all_provider_names

from shared.events import Event
from shared.events.chat import ChatMessageEvent
from shared.events.error import ErrorEvent
from shared.events.auth import (
    LoginRequiredEvent,
    LoginCompletedEvent,
    LoginFailedEvent,
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

def handle_event(event: Event) -> bool:
    """"""

    ephemeral: DeltaGenerator = st.session_state.ephemeral_container
        
    # ==========================
    #  Chat messages (persist)
    # ==========================
    if isinstance(event, ChatMessageEvent):
        st.session_state.ui_state["login_in_progress"] = False
        st.session_state.ui_state["login_message"] = None
        st.session_state.ui_state["login_url"] = None

        content = event.content

        if isinstance(content, list):
            content = content[0].get("text")

        if ephemeral:
            ephemeral.markdown(content)       

        st.session_state.messages.append(
            {
                "role": event.role,
                "content": content,
            }
        )

        st.session_state.ephemeral_container = None

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

    handle_event(event)


def on_error(exception: Exception) -> None:
    """"""

    pass


# ==========================
#        Session state
# ==========================

if "chat_id" not in st.session_state:
    st.session_state.chat_id = uuid.uuid4().hex

if "messages" not in st.session_state:
    st.session_state.messages = []

if "ephemeral_container" not in st.session_state:
    st.session_state.ephemeral_container = None

if "ws_client" not in st.session_state:
    st.session_state.ws_client = WSClient(
        websocket=None,
        session_id=uuid.uuid4().hex,
        websocket_uri="ws://0.0.0.0:8080/ws/chat"
    )

    logging.basicConfig(
        level=logging.INFO,
        format=""
    )

if "ui_state" not in st.session_state:
    st.session_state.ui_state = {
        "login_in_progress": False,
        "login_message": None,
        "login_url": None,

        "sidebar_visible": True,

        "selected_stores": [],
        "store_dialog_open": False,

        "chats": {
            "Chat - 1": st.session_state.messages
        },

        "current_chat": "Chat - 1",
    }


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
#          Sidebar
# ==========================

with st.sidebar:
    st.title("Settings")

    if st.button("🛒 Select Store", use_container_width=True):
        st.session_state.ui_state["store_dialog_open"] = True
        st.rerun()

    st.divider()

    st.title("Chats")

    if st.button("\u2795 New Chat", use_container_width=True):
        num_chat = len(st.session_state.ui_state["chats"].keys()) + 1
        chat_name = f"Chat - {num_chat}"

        new_chat_id = uuid.uuid4().hex

        st.session_state.chat_id = new_chat_id
        st.session_state.ui_state["chats"][chat_name] = []
        st.session_state.ui_state["current_chat"] = chat_name
        st.session_state.messages = st.session_state.ui_state["chats"][chat_name]

        st.rerun()

    if st.button("🧹 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("🗑️ Delete All Chats", use_container_width=True):
        new_chat_id = uuid.uuid4().hex

        st.session_state.chat_id = new_chat_id
        st.session_state.messages = []

        st.session_state.ui_state["chats"] = {
            "Chat - 1": st.session_state.messages
        }
        st.session_state.ui_state["current_chat"] = "Chat - 1"

        st.rerun()

    st.divider()

    for chat_name in st.session_state.ui_state["chats"]:
        if st.button(f"💬 {chat_name}", use_container_width=True):
            st.session_state.ui_state["current_chat"] = chat_name
            st.session_state.messages = (
                st.session_state.ui_state["chats"][chat_name]
            )

            st.rerun()


# ==========================
#    Render chat history
# ==========================

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ==========================
#   Store selection dialog
# ==========================

@st.dialog("Select Store")
def store_selector_dialog() -> None:
    """"""

    base_options: list[str] = all_provider_names()
    current_selection: list[str] = st.session_state.ui_state["selected_stores"]

    full_options: list[str] = list(set(base_options + current_selection))

    st.multiselect(
        "Select one or more stores or type to add new ones...",
        options=full_options,
        default=current_selection,
        key="store_multiselect",
        accept_new_options=True
    )
    st.caption((
        "⚠️ *Note: Searching within manually added stores "
        "take longer to process.*"
    ))

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Confirm"):
            st.session_state.ui_state["selected_stores"] = (
                st.session_state.store_multiselect
            )
            st.session_state.ui_state["store_dialog_open"] = False
            st.rerun()

    with col2:
        if st.button("❌ Cancel"):
            st.session_state.ui_state["store_dialog_open"] = False
            st.rerun()

    st.session_state.ui_state["store_dialog_open"] = False

if st.session_state.ui_state["store_dialog_open"]:
    store_selector_dialog()


# ==========================
#       Send message
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

    assistant_msg = st.chat_message("assistant")
    placeholder = assistant_msg.empty()

    st.session_state.ephemeral_container = placeholder

    metadata = {
        "selected_stores": st.session_state.ui_state["selected_stores"],
        "chat_id": st.session_state.chat_id
    }

    try:
        with placeholder:
            placeholder.markdown("Thinking...")
            received_events = get_event_loop().run_until_complete(
                st.session_state.ws_client.send(
                    role="user",
                    message=prompt,
                    metadata=metadata,
                    on_event=on_event,
                    on_error=on_error,
                )
            )

        if received_events:
            st.rerun()
        
    except Exception as e:
        err = f"WebSocket Error: {e}"

        st.session_state.messages.append(
            {"role": "assistant", "content": f"⚠️ {err}"}
        )