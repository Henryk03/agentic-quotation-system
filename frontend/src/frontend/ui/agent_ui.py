
import time
import uuid
import asyncio
import logging
from functools import partial
from asyncio import AbstractEventLoop

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from frontend.config import settings
from frontend.frontend_utils.rest.client import RESTClient

from shared.events import Event
from shared.events.metadata import StoreMetadata
from shared.events.chat import ChatMessageEvent
from shared.events.error import ErrorEvent
from shared.events.credentials import StoreCredentialsEvent
from shared.provider.registry import (
    all_provider_names,
    support_autologin
)
from shared.events.clear import (
    ClearClientChatsEvent,
    ClearChatMessagesEvent
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


def save_message(
        role: str,
        content: str
    ) -> None:
    """"""

    if st.session_state.messages:
        st.session_state.messages.append(
            {
                "role": role,
                "content": content
            }
        )

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
            save_message(
                role = result.role,
                content = result.content
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
    st.session_state.ws_client = RESTClient(
        base_url = f"http://{settings.HOST}:{settings.PORT}",
        session_id = uuid.uuid4().hex
    )

    logging.basicConfig(
        level=logging.INFO,
        format=""
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
            "store_status": {}
        },

        "send_credentials_now": False,

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
        current = st.session_state.ui_state["current_chat"]
        chat = st.session_state.ui_state["chats"][current]

        chat["messages"].clear()
        st.session_state.messages = chat["messages"]

        # clear_messages_event: Event = ClearChatMessagesEvent(
        #     chat_id = st.session_state.chat_id
        # )

        # get_event_loop().run_until_complete(
        #     st.session_state.rest_client.send_and_wait(
        #         clear_messages_event
        #     )
        # )

        st.rerun()

    if st.button("🗑️ Delete All Chats", use_container_width=True):
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

        delete_chats_event: Event = ClearClientChatsEvent()

        get_event_loop().run_until_complete(
            st.session_state.rest_client.send_and_wait(
                delete_chats_event
            )
        )

        st.rerun()

    st.divider()

    for chat_name, chat in st.session_state.ui_state["chats"].items():
        if st.button(f"💬 {chat_name}", use_container_width=True):
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

    st.markdown(f"### Login credentials for **{store}**")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)
    show_err_message = False

    with col1:
        if st.button("💾 Save"):
            if username.strip() == "" or password.strip() == "":
                show_err_message = True
            
            else:
                state["credentials"][store] = {
                    "username": username,
                    "password": password
                }

                state["are_valid_credentials"] = True

                state["pending_stores"].remove(store)
                state["current_store"] = (
                    state["pending_stores"][0]
                    if state["pending_stores"] else None
                )

                if not state["current_store"]:
                    st.session_state.ui_state["autologin_dialog_open"] = False
                    st.session_state.ui_state["send_credentials_now"] = True

                st.rerun()

    with col2:
        if st.button("↪️ Skip"):
            state["pending_stores"].remove(store)
            state["current_store"] = (
                state["pending_stores"][0]
                if state["pending_stores"] else None
            )

            if not state["current_store"]:
                st.session_state.ui_state["autologin_dialog_open"] = False

            st.rerun()

    if show_err_message:
        st.error(
            "⛔️ Please set both **Username** and "
            "**Password** to save or press **Skip**."
        )


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

            validated_stores = (
                st.session_state.ui_state["autologin"]["validated_stores"]
            )

            st.session_state.ui_state["selected_stores"] = selected_stores
            st.session_state.ui_state["custom_store_urls"] = custom_store_urls
            st.session_state.ui_state["results_per_item"] = results_per_item

            autologin_stores: list[str] = [
                s for s in selected_stores 
                if support_autologin(s) and s not in validated_stores
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

# if st.session_state.ui_state["send_credentials_now"]:
#     credentials_event: Event = AutoLoginCredentialsEvent(
#         credentials = st.session_state.ui_state["autologin"]["credentials"]
#     )

#     for _ in range(2):
#         received_event = get_event_loop().run_until_complete(
#             st.session_state.rest_client.send_and_wait(
#                 credentials_event
#             )
#         )

#         if received_event:
#             break

#     st.session_state.ui_state["send_credentials_now"] = False

#     st.rerun()


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
    with st.chat_message("user"):
        st.markdown(prompt)

    save_message(
        role = "user",
        content = prompt.strip()
    )

    assistant_msg: DeltaGenerator = st.chat_message("assistant")
    placeholder: DeltaGenerator = assistant_msg.empty()

    st.session_state.ephemeral_container = placeholder

    metadata: StoreMetadata = StoreMetadata(
        selected_stores = st.session_state.ui_state["selected_stores"],
        selected_external_store_urls = st.session_state.ui_state["custom_urls"],
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
                    event
                )
            )

            process_result(result)
            st.rerun()
        
        except Exception as e:
            err: str = f"Error: {str(e)}"

            placeholder.error(err)

            save_message(
                role = "assistant",
                content = f"⚠️  {err}"
            )