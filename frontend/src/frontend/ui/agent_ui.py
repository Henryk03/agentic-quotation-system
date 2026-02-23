
import time
import uuid
import asyncio
import logging
from functools import partial
from asyncio import AbstractEventLoop
from typing import Any

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from frontend.config import settings
from frontend.frontend_utils.rest.client import RESTClient

from shared.events import Event
from shared.events.metadata import StoreMetadata, BaseMetadata
from shared.events.chat import ChatMessageEvent
from shared.events.credentials import StoreCredentialsEvent
from shared.events.login import (
    StoreLoginResult, 
    CredentialsLoginResultEvent,
    LoginStatusResultEvent,
    CheckLoginStatusEvent
)
from shared.provider.registry import (
    all_provider_names,
    support_autologin
)
from shared.events.clear import (
    DeleteClientChatsEvent,
    ClearChatMessagesEvent,
    ClearChatMessagesResultEvent,
    DeleteClientChatsResultEvent
)


# ==========================
#          Helpers
# ==========================

def get_event_loop() -> AbstractEventLoop:
    """"""

    if "loop" not in st.session_state:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        st.session_state.loop = loop

    return st.session_state.loop


def close_dialog(
        flag_key: str
    ) -> None:
    """"""

    st.session_state.ui_state[flag_key] = False


def __move_to_next_store(
        store: str,
        state: dict[str, Any]
    ) -> None:
    """"""

    state["pending_stores"].remove(store)
    state["current_store"] = (
        state["pending_stores"][0]
        if state["pending_stores"] else None
    )

    if not state["current_store"]:
        st.session_state.ui_state["autologin_dialog_open"] = False


def __validate_store(
        store: str,
        state: dict[str, Any]
    ) -> None:
    """"""

    state["validated_stores"].add(store)


def __invalidate_store(
        store: str,
        state: dict[str, Any]
    ) -> None:
    """"""

    _ = state["validated_stores"].discard(store)

# ==========================
#     Message animation
# ==========================

def stream_data(
        text: str, 
        placeholder: DeltaGenerator
    ) -> None:
    """"""

    full_response = ""

    for chunk in text.split(" "):
        full_response += chunk + " "
        time.sleep(0.05)
        placeholder.markdown(full_response + "▌")

    placeholder.markdown(full_response)


# ==========================
#     Result processing
# ==========================

def process_result(
        result: Event
    ) -> None:
    """"""

    ephemeral: DeltaGenerator = (
        st.session_state.ephemeral_container
    )
        
    match result:
        case ChatMessageEvent():
            st.session_state.messages.append(
                {
                    "role": result.role,
                    "content": result.content
                }
            )

            stream_data(
                result.content,
                ephemeral
            )


# ==========================
#        Session state
# ==========================

if "ephemeral_container" not in st.session_state:
    st.session_state.ephemeral_container = None

if "rest_client" not in st.session_state:
    st.session_state.rest_client = RESTClient(
        base_url = f"http://127.0.0.1:{settings.PORT}",
        client_id = uuid.uuid4().hex
    )

if "ui_state" not in st.session_state:
    chat_id: str = uuid.uuid4().hex

    st.session_state.ui_state = {
        "selected_stores": [],
        "custom_store_urls": [],
        "results_per_item": 1,

        "store_dialog_open": False,
        "autologin_dialog_open": False,

        "autologin": {
            "pending_stores": [],
            "current_store": None,
            "credentials": {},
            "validated_stores": set(),
            "phase": "input",
            "login_result": None
        },

        "chats": {
            "Chat - 1": {
                "chat_id": chat_id,
                "messages": []
            }
        },

        "current_chat": "Chat - 1",
    }

    st.session_state.chat_id = chat_id
    st.session_state.messages = (
        st.session_state.ui_state["chats"]["Chat - 1"]["messages"]
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
#          Sidebar
# ==========================

with st.sidebar:
    st.title("Settings")

    if st.button("🛒 Select Store", use_container_width = True):
        st.session_state.ui_state["store_dialog_open"] = True
        st.rerun()

    st.divider()

    st.title("Chats")

    if st.button("\u2795 New Chat", use_container_width=True):
        chats = st.session_state.ui_state["chats"]
        chat_number = len(chats) + 1

        chat_name = f"Chat - {chat_number}"
        new_chat_id = uuid.uuid4().hex

        chats[chat_name] = {
            "chat_id": new_chat_id,
            "messages": []
        }

        st.session_state.ui_state["current_chat"] = chat_name
        st.session_state.chat_id = new_chat_id
        st.session_state.messages = chats[chat_name]["messages"]

        st.rerun()

    if st.button("🧹 Clear Chat", use_container_width=True):
        clear_messages_event: Event = ClearChatMessagesEvent(
            metadata = BaseMetadata(
                chat_id = st.session_state.chat_id
            )
        )

        clear_messages_result_event: Event = (
            get_event_loop().run_until_complete(
                st.session_state.rest_client.send_and_wait(
                    clear_messages_event
                )
            )
        )

        if isinstance(clear_messages_result_event, ClearChatMessagesResultEvent):
            if clear_messages_result_event.success:
                current = st.session_state.ui_state["current_chat"]
                chat = st.session_state.ui_state["chats"][current]

                chat["messages"].clear()
                st.session_state.messages = chat["messages"]

                st.rerun()

            else:
                pass        # decidere cosa fare

    if st.button("🗑️ Delete All Chats", use_container_width=True):
        delete_chats_event: Event = DeleteClientChatsEvent()

        delete_chat_result_event: Event = (
            get_event_loop().run_until_complete(
                st.session_state.rest_client.send_and_wait(
                    delete_chats_event
                )
            )
        )

        if isinstance(delete_chat_result_event, DeleteClientChatsResultEvent):
            if delete_chat_result_event.success:
                new_chat_id = uuid.uuid4().hex

                st.session_state.ui_state["chats"] = {
                    "Chat - 1": {
                        "chat_id": new_chat_id,
                        "messages": []
                    }
                }

                st.session_state.ui_state["current_chat"] = "Chat - 1"
                st.session_state.chat_id = new_chat_id
                st.session_state.messages = (
                    st.session_state.ui_state["chats"]["Chat - 1"]["messages"]
                )

                st.rerun()

            else:
                pass        # decidere anche qui cosa fare

    st.divider()

    for chat_name, chat in st.session_state.ui_state["chats"].items():
        is_active: bool = chat_name == st.session_state.ui_state["current_chat"]

        label: str = f"💬 {chat_name}"

        if is_active:
            label = f"👉 {chat_name}"

        if st.button(label, use_container_width = True):
            st.session_state.ui_state["current_chat"] = chat_name
            st.session_state.chat_id = chat["chat_id"]
            st.session_state.messages = chat["messages"]

            st.rerun()


# ==========================
#   Store related dialogs
# ==========================

@st.dialog(
    "Auto-login credentials",
    on_dismiss=partial(
        close_dialog,
        "autologin_dialog_open"
    )
)
def insert_autologin_credentials() -> None:
    """"""

    state = st.session_state.ui_state["autologin"]
    store = state["current_store"]

    st.markdown(f"### 🔑 Login credentials for **{store}**")

    if state["phase"] == "checking":
        st.info("Checking login status...")

        result_event: Event = get_event_loop().run_until_complete(
            st.session_state.rest_client.send_and_wait(
                CheckLoginStatusEvent(
                    store = store
                )
            )
        )

        if isinstance(result_event, LoginStatusResultEvent):
            result: StoreLoginResult = result_event.result
            state["login_result"] = result

            if result.success:
                state["phase"] = "validated"

            elif result.minutes_left and result.minutes_left > 0:
                state["phase"] = "cooldown"

            else:
                state["phase"] = "input"

        st.rerun()

    elif state["phase"] == "validated":
        # __validate_store(store, state)
        __move_to_next_store(store, state)

        state["phase"] = "checking"

        st.rerun()

    elif state["phase"] == "input":
        username = st.text_input("Email or Username")
        password = st.text_input("Password", type="password")

        col1, col2 = st.columns(2)
        show_error = False

        with col1:
            if st.button("💾 Save & Login"):
                if not username.strip() or not password.strip():
                    show_error = True

                else:
                    state["credentials"][store] = {
                        "username": username,
                        "password": password
                    }

                    state["phase"] = "processing"
                    st.rerun()

        with col2:
            if st.button("↪️ Skip"):
                __move_to_next_store(store, state)

                state["phase"] = "checking"
                st.rerun()

        if show_error:
            st.error(
                "⛔️ Please set both **Username** and "
                "**Password** or press **Skip**."
            )

    elif state["phase"] == "processing":
        st.info("Signing in... please wait.")

        result_event: Event = get_event_loop().run_until_complete(
            st.session_state.rest_client.send_and_wait(
                StoreCredentialsEvent(
                    credentials = {
                        store: state["credentials"][store]
                    }
                )
            )
        )

        if isinstance(result_event, CredentialsLoginResultEvent):
            store_result = result_event.results[0]
            state["login_result"] = store_result

            if store_result.success:
                state["phase"] = "validated"

            elif store_result.minutes_left and store_result.minutes_left > 0:
                state["phase"] = "cooldown"

            else:
                state["phase"] = "result"

        st.rerun()

    elif state["phase"] == "cooldown":
        result = state["login_result"]

        st.error(f"❌ Store temporarily locked")

        st.markdown(
            f"⏳ Please try again in "
            f"**{result.minutes_left} minute(s)**."
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Check again"):
                state["phase"] = "checking"
                st.rerun()

        with col2:
            if st.button("↪️ Skip"):
                __move_to_next_store(store, state)
                state["phase"] = "checking"
                st.rerun()

        with col3:
            if st.button("❌ Close"):
                st.session_state.ui_state["autologin_dialog_open"] = False
                st.rerun()

    elif state["phase"] == "result":
        result = state["login_result"]

        st.error(f"❌ We couldn't sign you in to **{store}**.")

        if result.attempts_left is not None:
            if result.attempts_left > 0:
                st.markdown(
                    f"* You have **{result.attempts_left} attempt(s)** remaining."
                )

            else:
                st.markdown(
                    "* You've used all available login attempts."
                )

        col1, col2, col3 = st.columns(3)

        with col1:
            if result.attempts_left and result.attempts_left > 0:
                if st.button("🔄 Try again"):
                    state["phase"] = "input"
                    st.rerun()

            else:
                if st.button("🔄 Check again"):
                    state["phase"] = "checking"
                    st.rerun()

        with col2:
            if st.button("↪️ Skip"):
                __move_to_next_store(store, state)
                state["phase"] = "checking"
                st.rerun()

        with col3:
            if st.button("❌ Close"):
                st.session_state.ui_state["autologin_dialog_open"] = False
                st.rerun()


@st.dialog(
    "Select Store",
    on_dismiss=partial(
        close_dialog,
        "store_dialog_open"
    )
)
def store_selector_dialog() -> None:
    """"""

    base_options: list[str] = all_provider_names()
    current_selection: list[str] = st.session_state.ui_state[
        "selected_stores"
    ]

    full_options: list[str] = list(
        set(base_options + current_selection)
    )

    st.multiselect(
        "Supported Stores",
        options = full_options,
        default = current_selection,
        key = "store_multiselect"
    )

    base_custom_options: list[str] = ["https://amazon.com"]
    current_custom_selection: list[str] = st.session_state.ui_state[
        "custom_store_urls"
    ]

    full_custom_options: list[str] = list(
        set(base_custom_options + current_custom_selection)
    )

    st.multiselect(
        "Custom Store URLs",
        options = full_custom_options,
        default = current_custom_selection,
        key = "store_multiselect_computer_use",
        placeholder = "https://store-example.com",
        accept_new_options = True
    )

    st.caption(
        (
            "⚠️ **Note**: Official integrations are fully optimized. "
            "Custom links use experimental technology and may have "
            "inconsistent results."
        )
    )

    results_per_item: int = st.select_slider(
        "Items to retrieve per store",
        options = list(range(1, 6)),
        value = st.session_state.ui_state["results_per_item"],
        help = (
            "Define how many products to search for in each store. "
            "Note that higher values will significantly increase total "
            "execution time."
        )
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Confirm"):
            selected_stores = st.session_state.store_multiselect
            custom_store_urls = st.session_state.store_multiselect_computer_use

            st.session_state.ui_state["selected_stores"] = selected_stores
            st.session_state.ui_state["custom_store_urls"] = custom_store_urls
            st.session_state.ui_state["results_per_item"] = results_per_item

            autologin_stores: list[str] = [
                s for s in selected_stores if support_autologin(s)
            ]

            st.session_state.ui_state["autologin"]["pending_stores"] = autologin_stores
            st.session_state.ui_state["autologin"]["current_store"] = (
                autologin_stores[0] if autologin_stores else None
            )

            st.session_state.ui_state["store_dialog_open"] = False
            st.session_state.ui_state["autologin_dialog_open"] = bool(
                autologin_stores
            )

            st.rerun()

    with col2:
        if st.button("❌ Cancel"):
            st.session_state.ui_state["store_dialog_open"] = False

            st.rerun()

    st.session_state.ui_state["store_dialog_open"] = False


if st.session_state.ui_state["store_dialog_open"]:
    store_selector_dialog()

if st.session_state.ui_state["autologin_dialog_open"]:
    insert_autologin_credentials()


# ==========================
#    Render chat history
# ==========================

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])    


# ==========================
#       Send message
# ==========================

prompt: str | None = st.chat_input("Type a message...")

if prompt:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt.strip()
        }
    )
    
    with st.chat_message("user"):
        st.markdown(prompt)

    assistant_msg: DeltaGenerator = st.chat_message("assistant")
    placeholder: DeltaGenerator = assistant_msg.empty()

    st.session_state.ephemeral_container = placeholder

    timeout: float = 120.0

    metadata: StoreMetadata = StoreMetadata(
        selected_stores = st.session_state.ui_state["selected_stores"],
        selected_external_store_urls = st.session_state.ui_state["custom_store_urls"],
        chat_id = st.session_state.chat_id,
        items_per_store = st.session_state.ui_state["results_per_item"]
    )

    event: Event = ChatMessageEvent(
        role = "user",
        content = prompt.strip(),
        metadata = metadata
    )

    with placeholder:
        placeholder.markdown("Thinking...")

        try:
            result: Event = get_event_loop().run_until_complete(
                st.session_state.rest_client.send_and_wait(
                    event,
                    timeout = (
                        300.0 
                        if st.session_state.ui_state["custom_store_urls"]
                        else 120.0
                    )
                )
            )

            process_result(result)
            st.rerun()
        
        except Exception as e:
            err: str = f"Error: {str(e)}"

            placeholder.error(err)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"⚠️  {err}"
                }
            )