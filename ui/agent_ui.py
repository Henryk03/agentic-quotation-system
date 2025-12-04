import json
from typing import Any, Dict, List, Optional

import requests
import streamlit as st


DEFAULT_BASE_URL = "http://agent-backend:8080"
DEFAULT_MODEL = "mio-modello"


def api_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + path


def fetch_models(base_url: str, timeout: float = 5.0) -> List[str]:
    try:
        r = requests.get(api_url(base_url, "/v1/models"), timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return [m.get("id", "") for m in data.get("data", []) if m.get("id")]
    except Exception:
        return []


def chat_completion(
    base_url: str,
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 60.0,
) -> str:
    payload = {"model": model, "messages": messages}

    r = requests.post(
        api_url(base_url, "/v1/chat/completions"),
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=timeout,
    )
    r.raise_for_status()
    data: Dict[str, Any] = r.json()

    # OpenAI-like response: choices[0].message.content
    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        # Fallbacks for slightly different shapes
        if "choices" in data and data["choices"]:
            choice0 = data["choices"][0]
            msg = choice0.get("message") or {}
            content = msg.get("content")
            if isinstance(content, str):
                return content
        return f"[Unexpected response shape]\n{json.dumps(data, indent=2)}"


def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []  # [{role, content}]
    if "base_url" not in st.session_state:
        st.session_state.base_url = DEFAULT_BASE_URL
    if "model" not in st.session_state:
        st.session_state.model = DEFAULT_MODEL


init_state()

st.set_page_config(page_title="Agent Chat", page_icon="🤖", layout="centered")
st.title("🤖 Agent Chat")

with st.sidebar:
    st.header("Settings")
    st.session_state.base_url = st.text_input("API base URL", st.session_state.base_url)

    # Try to populate model list from /v1/models (optional)
    models = fetch_models(st.session_state.base_url)
    if models:
        st.session_state.model = st.selectbox(
            "Model",
            options=models,
            index=models.index(st.session_state.model) if st.session_state.model in models else 0,
        )
    else:
        st.session_state.model = st.text_input("Model", st.session_state.model)

    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("Tip: Start FastAPI first, then run Streamlit.")


# Render chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])


prompt: Optional[str] = st.chat_input("Type a message...")
if prompt:
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get assistant response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Thinking…")

        try:
            # Note: your FastAPI code currently uses ONLY the last user message,
            # but sending full history keeps this UI compatible if you later change the API.
            answer = chat_completion(
                base_url=st.session_state.base_url,
                model=st.session_state.model,
                messages=st.session_state.messages,
            )
            placeholder.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

        except requests.RequestException as e:
            err = f"Request failed: {e}"
            placeholder.error(err)
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ {err}"})
        except Exception as e:
            err = f"Unexpected error: {e}"
            placeholder.error(err)
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ {err}"})
 