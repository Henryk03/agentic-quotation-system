#!/bin/bash

# ====================================================
#  Script to create separate virtual environments for
#  frontend and backend using Python 3.13 and install
#  their dependencies, including Playwright browsers.
# ====================================================

set -euo pipefail

# -----------------------------
#      Error exit function
# -----------------------------
function error_exit {
    echo "ERROR: $1" >&2
    exit 1
}

# -----------------------------
#   Animated install function
# -----------------------------
function animated_install {
    local MESSAGE="$1"
    local CMD="$2"
    local DOTS=0

    # Start animation in background
    {
        while true; do
            DOTS=$(( (DOTS + 1) % 4 ))  # 0..3 dots
            # Print message + dots without newline
            printf "\r%s" "$MESSAGE"
            for ((i=0;i<DOTS;i++)); do
                printf "."
            done
            # Add spaces to overwrite leftover dots
            for ((i=DOTS;i<3;i++)); do
                printf " "
            done
            sleep 0.5
        done
    } &
    ANIM_PID=$!

    # Run the actual command
    eval "$CMD"
    CMD_EXIT=$?

    # Stop animation
    kill $ANIM_PID &> /dev/null
    wait $ANIM_PID 2>/dev/null || true

    # Print final message
    if [ $CMD_EXIT -eq 0 ]; then
        echo -e "\r$MESSAGE... done!"
    else
        echo -e "\r$MESSAGE... failed!"
        exit $CMD_EXIT
    fi
}

# -----------------------------
#       Check Python 3.13
# -----------------------------
PYTHON_VERSION="python3.13"
if ! command -v $PYTHON_VERSION &> /dev/null
then
    error_exit "$PYTHON_VERSION not found. Please install Python 3.13."
fi

# -----------------------------
#            Paths
# -----------------------------
ROOT_DIR="$(pwd)"
VENVS_DIR="$ROOT_DIR/venvs"

# -----------------------------
#    Create venvs directory
# -----------------------------
animated_install "Creating venvs directory" "mkdir -p $VENVS_DIR"

# -----------------------------
#   Function to create a venv
# -----------------------------
function create_venv {
    local NAME=$1
    local REQ_DIR=$2
    local VENV_PATH="$VENVS_DIR/$NAME"

    animated_install "Creating virtual environment for $NAME" "$PYTHON_VERSION -m venv $VENV_PATH"

    source "$VENV_PATH/bin/activate" || error_exit "Failed to activate venv $NAME"

    animated_install "Upgrading pip in $NAME" "pip install --upgrade pip --quiet"

    if [ -f "$REQ_DIR/requirements.txt" ]; then
        animated_install "Installing dependencies for $NAME" "pip install -r $REQ_DIR/requirements.txt --quiet"

        if pip show playwright &> /dev/null; then
            echo "Installing chromium for Playwright in $NAME (may take a while)..."
            python -m playwright install chromium
        fi
    else
        echo "WARNING: No requirements.txt found in $REQ_DIR"
    fi

    deactivate

    echo "Virtual environment $NAME is ready at $VENV_PATH"
}

# -----------------------------
#  Backend and frontend venvs
# -----------------------------
create_venv "backend" "$ROOT_DIR/requirements/backend"
create_venv "frontend" "$ROOT_DIR/requirements/frontend"

# -----------------------------
#            Finish
# -----------------------------
echo "All virtual environments are ready!"
echo "You can now run 'start_agentic_system.sh' to start the system."