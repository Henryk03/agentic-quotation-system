
# Frontend

## Overview

The frontend is responsible for rendering the user interface and communicating with the backend through REST.

It allows users to submit requests, monitor execution progress, and visualize results returned by the agent running on the server.

The frontend does not execute automation logic directly; it acts as an interaction and visualization layer.

## Responsibilities

- Render the user interface
- Send events to the backend
- Poll for execution results
- Display job status and responses
- Reflect provider capabilities exposed by the `shared` package

## Architecture

### UI Layer

Contains the Streamlit-based user interface.

This layer handles:

- User interaction
- Event submission
- Result visualization
- State management within the UI

### REST Client Layer

Implements the HTTP client responsible for communicating with the backend. It:

- Sends job creation requests
- Polls execution status
- Retrieves execution results

This layer abstracts backend communication from the UI components.


### Provider Integration Layer

The frontend depends on the `shared` package for:

- Access to provider definitions
- Store metadata
- Login requirements
- Shared domain abstractions

Providers are not implemented in this codebase.
They are consumed as a source of truth for UI representation and validation logic.


## Technology Stack

- Python 3.13.x
- [Streamlit](https://streamlit.io)
- uv (recommended package & dependency manager)

## Project Structure

- `ui/`
    - Contains the main Streamlit UI implementation.

- `frontend_utils/`
    - Contains:
	    - REST client abstraction

- `config.py`
    - Environment configuration abstraction.

## Setup

All command examples use `bash` syntax (Linux, macOS, Git Bash, or WSL). If using Windows PowerShell or CMD, adapt commands accordingly.

### Using uv (Recommended)

```bash
uv sync
source .venv/bin/activate
```

### Using pip (Alternative)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

**Note**: When using `pip`, ensure you are using Python 3.13.x when creating the virtual environment.

## Environment Configuration

After setting up the virtual environment, configure environment variables.

Create the `.env` file:

```bash
cp .env.example .env
```

Edit the file according to the provided comments.

## Running the Frontend

Before running the application, move into the `src` directory.

### Production mode

```bash
python -m frontend
```

This starts the Streamlit interface and connects to the configured backend instance.

Ensure that the backend is running before starting the frontend.