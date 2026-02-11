
import time
import uuid
import asyncio
import logging
from functools import partial

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from frontend.config import settings
from frontend.frontend_utils.websocket.client import WSClient

from shared.events import Event
from shared.events.chat import ChatMessageEvent
from shared.events.error import ErrorEvent
from shared.events.login import LoginRequiredEvent
from shared.provider.registry import (
    all_provider_names,
    support_autologin
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


def close_dialog(
        flag_key: str
    ) -> None:
    """"""

    st.session_state.ui_state[flag_key] = False

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
#      Event handling
# ==========================

def handle_event(
        event: Event
    ) -> bool:
    """"""

    ephemeral: DeltaGenerator = st.session_state.ephemeral_container
    login_open: bool = st.session_state.ui_state["login_dialog"]["open"]
        
    # ==========================
    #  Chat messages (persist)
    # ==========================
    if isinstance(event, ChatMessageEvent):
        if login_open:
            st.session_state.messages.append(
                {
                    "role": event.role,
                    "content": event.content,
                }
            )
            return True
        
        st.session_state.messages.append(
            {
                "role": event.role,
                "content": event.content,
            }
        )

        if ephemeral:
            stream_data(event.content, ephemeral)  
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

        if ephemeral:
            ephemeral.error(event.message)

        return True
    
    # ==========================
    #   Login flow (temporary)
    # ==========================
    if isinstance(event, LoginRequiredEvent):
        st.session_state.ui_state["login_dialog"].update(
            {
                "open": True,
                "status": "waiting",
                "provider": event.provider,
                "login_url": event.login_url,
                "message": "Manual login is required to continue"
            }
        )
        
        return True
    
    return False


def on_event(event: Event) -> bool:
    """"""

    return handle_event(event)


def on_error(exception: Exception) -> None:
    """"""

    pass


# ==========================
#        Session state
# ==========================

if "ephemeral_container" not in st.session_state:
    st.session_state.ephemeral_container = None

if "ws_client" not in st.session_state:
    st.session_state.ws_client = WSClient(
        websocket=None,
        session_id=uuid.uuid4().hex,
        websocket_uri=f"ws://{settings.HOST}:{settings.PORT}/ws/chat"
    )

    logging.basicConfig(
        level=logging.INFO,
        format=""
    )

if "ui_state" not in st.session_state:
    chat_id: str = uuid.uuid4().hex

    st.session_state.ui_state = {
        "selected_stores": [],          # list for supported stores (automation)
        "custom_urls": [],              # list for non supported stores (computer use)
        "results_per_item": 1,
        "store_dialog_open": False,
        "autologin_dialog_open": False,

        "login_dialog": {
            "open": False,
            "status": "idle",           # idle | waiting | in_progress | success | error | cancelled
            "provider": None,
            "login_url": None,
            "_close_next_run": False
        },

        "autologin": {
            "pending_stores": [],
            "current_store": None,
            "credentials": {}
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

    if st.button("🛒 Select Store", use_container_width=True):
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

        get_event_loop().run_until_complete(
            st.session_state.ws_client.send_clear_messages(
                st.session_state.chat_id
            )
        )

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

        get_event_loop().run_until_complete(
            st.session_state.ws_client.send_clear_chats()
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
#    Login related dialog
# ==========================

@st.dialog("Login required")
def login_dialog() -> None:
    """"""

    login = st.session_state.ui_state["login_dialog"]

    st.markdown(f"### Manual login required for **{login["provider"]}**")

    status = st.empty()

    match login["status"]:
        case "waiting":
            status.info("Waiting for confirmation")

        case "in_progress":
            status.warning("🔄 Login in progress...")

        case "success":
            status.success("✅ Login completed successfully")

        case "error":
            status.error(f"❌ Login failed: {login["message"]}")

        case "cancelled":
            status.warning("⚠️ Login cancelled by user")

        case _:
            status.error("❌ Invalid status")

    col1, col2 = st.columns(2)

    if login["status"] == "waiting":
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Proceed"):
                st.session_state.ui_state["login_dialog"]["status"] = "in_progress"
                st.rerun()

        with col2:
            if st.button("❌ Cancel"):
                st.session_state.ui_state["login_dialog"].update(
                    {
                        "open": True,
                        "status": "cancelled",
                        "provider": login["provider"],
                        "login_url": None
                    }
                )
                st.rerun()


if st.session_state.ui_state["login_dialog"]["open"]:
    login_dialog()

if st.session_state.ui_state["login_dialog"]["status"] == "cancelled":
    metadata = {
        "chat_id": st.session_state.chat_id,
        "selected_stores": st.session_state.ui_state["selected_stores"]
    }

    _ = get_event_loop().run_until_complete(
        st.session_state.ws_client.handle_login_cancelled(
            st.session_state.ui_state["login_dialog"]["provider"],
            metadata,
            on_event,
            on_error
        )
    )

    st.session_state.ui_state["login_dialog"].update(
        {
            "open": False,
            "status": "idle",
            "provider": None,
            "login_url": None
        }
    )

    st.rerun()

if st.session_state.ui_state["login_dialog"]["status"] == "in_progress":
    try:
        ok: bool = get_event_loop().run_until_complete(
            st.session_state.ws_client.handle_login(
                st.session_state.ui_state["login_dialog"]["provider"],
                st.session_state.ui_state["login_dialog"]["login_url"],
                st.session_state.chat_id,
                st.session_state.ui_state["selected_stores"],
                on_event,
                on_error
            )
        )

        if ok:
            st.session_state.ui_state["login_dialog"]["status"] = "success"

        else:
            st.session_state.ui_state["login_dialog"]["status"] = "error",
            st.session_state.ui_state["login_dialog"]["message"] = (
                "Login failed or timeout"
            )

    except Exception as e:
        st.session_state.ui_state["login_dialog"]["status"] = "error"
        st.session_state.ui_state["login_dialog"]["message"] = str(e)

    st.rerun()

if st.session_state.ui_state["login_dialog"]["status"] in ("success", "error"):
    if not st.session_state.ui_state["login_dialog"]["_close_next_run"]:
        st.session_state.ui_state["login_dialog"]["_close_next_run"] = True
        st.rerun()

    else:
        time.sleep(2)

        st.session_state.ui_state["login_dialog"].update(
            {
                "open": False,
                "status": "idle",
                "provider": None,
                "login_url": None,
                "message": None,
                "_close_next_run": False,
            }
        )

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
    current_selection: list[str] = st.session_state.ui_state["selected_stores"]

    full_options: list[str] = list(set(base_options + current_selection))

    st.multiselect(
        "Supported Stores",
        options=full_options,
        default=current_selection,
        key="store_multiselect"
    )

    st.multiselect(
        "Custom Store URLs",
        options="https://amazon.com",
        key="store_multiselect_computer_use",
        placeholder="https://store-example.com",
        accept_new_options=True
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
        options = list(range(1, 11)),
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
            custom_urls = st.session_state.store_multiselect_computer_use

            st.session_state.ui_state["selected_stores"] = selected_stores
            st.session_state.ui_state["custom_urls"] = custom_urls
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

if st.session_state.ui_state["send_credentials_now"]:
    for _ in range(2):
        received_event = get_event_loop().run_until_complete(
            st.session_state.ws_client.send_credentials(
                st.session_state.ui_state["autologin"]["credentials"]
            )
        )

        if received_event:
            break

    st.session_state.ui_state["send_credentials_now"] = False

    st.rerun()


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
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    assistant_msg = st.chat_message("assistant")
    placeholder = assistant_msg.empty()

    st.session_state.ephemeral_container = placeholder

    metadata: dict[str, list[str] | str | int] = {
        "selected_stores": st.session_state.ui_state["selected_stores"],
        "custom_urls": st.session_state.ui_state["custom_urls"],
        "chat_id": st.session_state.chat_id,
        "items_per_store": st.session_state.ui_state["results_per_item"]
    }

    with placeholder:
        placeholder.markdown("Thinking...")

        try:
            received_events: bool = get_event_loop().run_until_complete(
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

            placeholder.error(err)