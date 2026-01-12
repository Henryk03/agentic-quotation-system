
import time

import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from playwright.sync_api import sync_playwright

from shared.events import Event
from shared.events.chat import ChatMessageEvent
from shared.events.error import ErrorEvent
from shared.events.auth import (
    LoginRequiredEvent,
    LoginCompletedEvent,
    LoginFailedEvent
)


def handle_event(
        *,
        event: Event,
        placeholder: DeltaGenerator | None = None,
    ) -> None:
    """"""

    # message
    if isinstance(event, ChatMessageEvent):
        with st.chat_message(event.role):

            # tool calls will be ignored
            if event.content:
                st.markdown(event.content)
                st.session_state.messages.append(
                    {
                        "role": event.role,
                        "content": event.content,
                    }
                )

        return

    # error
    if isinstance(event, ErrorEvent):
        st.error(event.message)
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"⚠️ {event.message}",
            }
        )

        return
    
    # login required
    if isinstance(event, LoginRequiredEvent):
        placeholder.warning(event.message)

        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=False,
                channel="chrome",
            )
            page = browser.new_page()
            page.goto(str(event.login_url))

        st.info(
            "Completa il login nel browser appena aperto "
            "e torna qui."
        )
        
        return

    # login completed
    if isinstance(event, LoginCompletedEvent):
        placeholder.success(event.message)
        return

    # login failed
    if isinstance(event, LoginFailedEvent):
        placeholder.error(
            f"❌ Login fallito ({event.provider})"
        )
        if event.reason:
            st.error(event.reason)
        return