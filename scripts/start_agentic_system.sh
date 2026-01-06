#!/bin/bash

# =====================================================
#  Script to run backend and frontend services locally
#  using Python virtual environments.
# =====================================================

set -euo pipefail

BACKEND_VENV="venvs/backend"
FRONTEND_VENV="venvs/frontend"

BACKEND_SCRIPT="websocket_server.websocket_agent_server"
FRONTEND_SCRIPT="ui/agent_ui.py"

if [ ! -d "$BACKEND_VENV" ]; then
    echo "ERROR: Backend venv not found at $BACKEND_VENV. Run setup_venvs.sh first."
    exit 1
fi

if [ ! -d "$FRONTEND_VENV" ]; then
    echo "ERROR: Frontend venv not found at $FRONTEND_VENV. Run setup_venvs.sh first."
    exit 1
fi

if [ -z "${GOOGLE_API_KEY:-}" ]; then
    echo "WARNING: GOOGLE_API_KEY not set. Some backend features may not work."
else
    export GOOGLE_API_KEY="$GOOGLE_API_KEY"
fi

echo "Starting backend..."
(
    source "$BACKEND_VENV/bin/activate"
    python -m "$BACKEND_SCRIPT"
) &

sleep 3

echo "Starting frontend (Streamlit)..."
(
    source "$FRONTEND_VENV/bin/activate"
    streamlit run "$FRONTEND_SCRIPT"
)