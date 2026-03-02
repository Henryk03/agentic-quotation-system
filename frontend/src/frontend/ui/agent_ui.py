
import time
import uuid
from functools import partial
from typing import Any

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from frontend.config import settings
from frontend.frontend_utils.rest.client import RESTClient

from shared.events import Event, ErrorEvent
from shared.events.metadata import BaseMetadata, StoreMetadata
from shared.events.chat import ChatMessageEvent
from shared.events.credentials import StoreCredentialsEvent
from shared.events.login import (
    CheckLoginStatusEvent,
    CredentialsLoginResultEvent,
    LoginStatusResultEvent,
    StoreLoginResult,
    TriggerAutoLoginEvent,
)
from shared.events.clear import (
    ClearChatMessagesEvent,
    ClearChatMessagesResultEvent,
    DeleteClientChatsEvent,
    DeleteClientChatsResultEvent,
)
from shared.provider.registry import (
    all_provider_names,
    support_autologin,
)
from shared.shared_utils.common import LoginStatus


# ==========================
#          Helpers
# ==========================

def send_event(
        event: Event
    ) -> Event:
    """
    Send an event to the backend through the REST client 
    and wait for a response.

    Parameters
    ----------
    event : Event
        The event instance to be sent to the backend.

    Returns
    -------
    Event
        The event returned by the backend after processing.

    Notes
    -----
    This function delegates the call to the REST client 
    stored in `st.session_state.rest_client` and blocks 
    until a response is received.
    """

    return st.session_state.rest_client.send_and_wait(
        event
    )


def close_dialog(
        flag_key: str
    ) -> None:
    """
    Close a dialog by updating the corresponding UI state flag.

    Parameters
    ----------
    flag_key : str
        The key in ``st.session_state.ui_state`` that controls 
        the dialog visibility.

    Returns
    -------
    None
    """

    st.session_state.ui_state[flag_key] = False


def __move_to_next_store(
        store: str,
        state: dict[str, Any]
    ) -> None:
    """
    Advance the auto-login workflow to the next pending store.

    Parameters
    ----------
    store : str
        The store that has just been processed.

    state : dict[str, Any]
        The auto-login state dictionary containing:
        - `pending_stores`
        - `current_store`
        - other workflow-related metadata.

    Returns
    -------
    None

    Notes
    -----
    If no more stores remain, the auto-login dialog is automatically 
    closed.
    """

    state["pending_stores"].remove(store)
    state["current_store"] = (
        state["pending_stores"][0]
        if state["pending_stores"] else None
    )

    if not state["current_store"]:
        st.session_state.ui_state["autologin_dialog_open"] = False


def __next_phase(
        result: StoreLoginResult
    ) -> str:
    """
    Determine the next UI phase based on a store login result.

    Parameters
    ----------
    result : StoreLoginResult
        The result of a login attempt for a specific store.

    Returns
    -------
    str
        The next phase of the auto-login workflow. Possible values 
        include:
        - `"success"`
        - `"input"`
        - `"autologin_attempt"`
        - `"failed"`
        - `"result"`

    Notes
    -----
    The phase is derived from ``result.status``.
    """

    match result.status:

        case LoginStatus.VALID:
            return "success"
        
        case LoginStatus.NEEDS_CREDENTIALS:
            return "input"
        
        case LoginStatus.AUTOLOGIN_REQUIRED:
            return "autologin_attempt"
        
        case LoginStatus.FAILED: 
            return "failed"
        
        case _:
            return "result"


def stream_data(
        text: str,
        placeholder: DeltaGenerator
    ) -> None:
    """
    Stream text progressively into a Streamlit placeholder.

    Parameters
    ----------
    text : str
        The full text response to display.
    placeholder : DeltaGenerator
        The Streamlit container where the text will be rendered.

    Returns
    -------
    None

    Notes
    -----
    The text is rendered word-by-word with a small delay to simulate
    streaming output. A trailing cursor indicator (▌) is displayed
    during streaming.
    """

    full_response: str = ""

    for chunk in text.split(" "):

        full_response += chunk + " "
        time.sleep(0.05)
        placeholder.markdown(full_response + "▌")

    placeholder.markdown(full_response)


# ==========================
#        Session state
# ==========================

if "ephemeral_container" not in st.session_state:

    st.session_state.ephemeral_container = None


if "rest_client" not in st.session_state:

    st.session_state.rest_client = RESTClient(
        base_url = f"http://{settings.HOST}:{settings.PORT}",
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
            "phase": "checking"
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
#     Result processing
# ==========================

def process_result(
        result: Event
    ) -> None:
    """
    Process a backend event and update the UI state accordingly.

    Parameters
    ----------
    result : Event
        The event returned by the backend.

    Returns
    -------
    None

    Notes
    -----
    The function handles multiple event types using structural pattern
    matching, including:

    - `ErrorEvent`
    - `ChatMessageEvent`
    - `LoginStatusResultEvent`
    - `CredentialsLoginResultEvent`
    - `ClearChatMessagesResultEvent`
    - `DeleteClientChatsResultEvent`

    Depending on the event type, the function may:
    - Update chat history
    - Modify auto-login workflow state
    - Reset chat sessions
    - Display error messages
    - Trigger a Streamlit rerun
    """

    ephemeral: DeltaGenerator = st.session_state.ephemeral_container
    state: dict[str, Any] = st.session_state.ui_state["autologin"]
        
    match result:

        # ----------------------- ERROR ------------------------
        case ErrorEvent():
            st.session_state.messages.append({
                "role": "assistant",
                "content": result.message
            })

            error_msg: str = f"❌ **Error**: {result.message}"
            ephemeral.error(error_msg)

            st.rerun()

        # ------------------------ CHAT ------------------------
        case ChatMessageEvent():
            st.session_state.messages.append({
                "role": result.role,
                "content": result.content
            })

            stream_data(
                result.content,
                ephemeral
            )

            st.rerun()

        # ----------------------- LOGIN ------------------------
        case LoginStatusResultEvent():
            state["phase"] = __next_phase(result.result)

            st.rerun()

        # -------------------- CREDENTIALS ---------------------
        case CredentialsLoginResultEvent():
            state["phase"] = __next_phase(result.results[0])
            
            st.rerun()

        # --------------------- CLEAR CHAT ---------------------
        case ClearChatMessagesResultEvent():            
            if result.success:
                current = st.session_state.ui_state["current_chat"]
                chat = st.session_state.ui_state["chats"][current]

                chat["messages"].clear()
                st.session_state.messages = chat["messages"]

                st.rerun()

            else:
                pass

        # -------------------- DELETE CHATS --------------------
        case DeleteClientChatsResultEvent():
            if result.success:
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
                pass

        case _:
            error_msg: str = "❌ Event not supported."

            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg
            })

            ephemeral.error(error_msg)

            st.rerun()


# ==========================
#        Page setup
# ==========================

st.set_page_config(
    page_title = "Agent Chat",
    page_icon = "🤖",
    layout = "centered",
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

    if st.button("\u2795 New Chat", use_container_width = True):
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

    if st.button("🧹 Clear Chat", use_container_width = True):
        clear_messages_result_event: Event = send_event(
            ClearChatMessagesEvent(
                metadata = BaseMetadata(
                    chat_id = st.session_state.chat_id
                )
            )
        )

        process_result(clear_messages_result_event)

    if st.button("🗑️ Delete All Chats", use_container_width = True):
        delete_chats_result_event: Event = send_event(
            DeleteClientChatsEvent()
        )

        process_result(delete_chats_result_event)

    st.divider()


    for chat_name, chat in st.session_state.ui_state["chats"].items():
        is_active: bool = (
            chat_name == st.session_state.ui_state["current_chat"]
        )

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
    on_dismiss = partial(
        close_dialog,
        "autologin_dialog_open"
    )
)
def insert_autologin_credentials() -> None:
    """
    Render and manage the auto-login credentials dialog.

    Returns
    -------
    None

    Notes
    -----
    This dialog drives the multi-phase auto-login workflow. 
    The behavior depends on the current `phase` stored in
    `st.session_state.ui_state["autologin"]`.

    Possible phases include:

    - `"checking"`
    - `"autologin_attempt"`
    - `"input"`
    - `"manual_processing"`
    - `"success"`
    - `"failed"`

    The function may trigger backend events and rerun the Streamlit app
    to advance the workflow.
    """

    state: dict[str, Any] = st.session_state.ui_state["autologin"]
    store: str = state["current_store"]

    phase: str = state.get("phase", "failed")

    match phase:

        case "success":
            st.success(
                f"✅ **{store}** authenticated, moving on..."
            )

            time.sleep(1.5)

            __move_to_next_store(store, state)
            state["phase"] = "checking"
            st.rerun()

        case "checking":
            st.info(f"🔍 Checking login status for **{store}**...")
            
            result_event = send_event(
                CheckLoginStatusEvent(
                    store = store
                )
            )
            
            process_result(result_event)

        case "autologin_attempt":
            st.info(f"🔄 Attempting to auto-login to **{store}**...")
            
            result_event = send_event(
                TriggerAutoLoginEvent(
                    store = store
                )
            )
            
            process_result(result_event)

        case "input":
            st.markdown(f"### 🔑 Credentials required for **{store}**")

            username: str = st.text_input("Email or Username")
            password: str = st.text_input("Password", type = "password")
            
            col1, col2 = st.columns(2)
            show_error: bool = False

            with col1:
                if st.button("💾 Save & Login"):
                    if not username.strip() or not password.strip():
                        show_error = True

                    else:
                        state["credentials"][store] = {
                            "username": username, 
                            "password": password
                        }

                        state["phase"] = "manual_processing"
                        st.rerun()

            with col2:
                if st.button("↪️ Skip this store"):
                    __move_to_next_store(store, state)
                    state["phase"] = "checking"
                    st.rerun()

            if show_error:
                st.error(
                    "⛔️ Both **username** and **password** are required."
                )

        case "manual_processing":
            st.info(f"🔐 Login in progress for **{store}**...")
            
            result_event = send_event(
                StoreCredentialsEvent(
                    credentials = {
                        store: state["credentials"][store]
                    }
                )
            )

            process_result(result_event)

        case "failed":
            st.error(f"❌ Unable to access **{store}**")
            
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🔄 Try again"):
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
    on_dismiss = partial(
        close_dialog,
        "store_dialog_open"
    )
)
def store_selector_dialog() -> None:
    """
    Render the store selection dialog.

    Returns
    -------
    None

    Notes
    -----
    Allows the user to:

    - Select supported stores
    - Provide custom store URLs
    - Configure the number of items to retrieve per store

    On confirmation, the function updates the global UI state and
    initializes the auto-login workflow for stores that support it.
    """

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
            custom_store_urls = (
                st.session_state.store_multiselect_computer_use
            )

            st.session_state.ui_state["selected_stores"] = selected_stores
            st.session_state.ui_state["custom_store_urls"] = custom_store_urls
            st.session_state.ui_state["results_per_item"] = results_per_item

            autologin_stores: list[str] = [
                s for s in selected_stores if support_autologin(s)
            ]

            st.session_state.ui_state["autologin"]["pending_stores"] = (
                autologin_stores
            )
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

    if st.session_state.ui_state["custom_store_urls"]:
        timeout = 300.0 * round(
            number = (st.session_state.ui_state["results_per_item"] / 2),
            ndigits = 1
        )

    else:
        timeout *= round(
            number = st.session_state.ui_state["results_per_item"],
            ndigits = 1
        )

    metadata: StoreMetadata = StoreMetadata(
        selected_stores = st.session_state.ui_state["selected_stores"],
        selected_external_store_urls = (
            st.session_state.ui_state["custom_store_urls"]
        ),
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
            result: Event = st.session_state.rest_client.send_and_wait(
                event,
                timeout = timeout
            )

            process_result(result)
        
        except Exception as e:
            process_result(
                ErrorEvent(
                    message = str(e)
                )
            )