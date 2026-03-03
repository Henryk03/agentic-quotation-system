
# Backend

## Overview

The backend is responsible for executing and orchestrating the agent together with its web automation tools.  
It exposes REST API endpoints, handles database persistence, and runs periodic cleanup operations.

This codebase coordinates the store/provider implementations defined in the `shared` package, while remaining independent from their concrete logic.  
The backend serves as the **core execution engine** of the entire system.

## Responsibilities

- Expose REST endpoints
- Orchestrate agent execution
- Manage provider interactions
- Persist essential data
- Dispatch and handle events
- Execute background maintenance tasks

## Architecture

### Agent Layer

Contains the LangChain-based agent implementation and its automation tools.

This layer includes:

- Prompt definitions
- Tool definitions
- Agent graph implementation
- Execution orchestration logic

The agent interacts with providers defined in the `shared` package.

### REST Layer

Provides the HTTP interface of the system.

The server exposes two main endpoints:

- A job creation endpoint used by the UI to submit a task
- A polling endpoint used by the UI to retrieve execution results

The REST layer acts as the bridge between the frontend and the agent execution pipeline.

### Database Layer

Responsible for persistence and structured data access.

Includes:

- ORM models (mapped classes and relationships)
- Repository layer for database operations
- Async PostgreSQL engine configuration
- Alembic migration support

This layer follows a structured separation between models and repositories to improve maintainability.


### Provider Layer

The backend depends on the shared package for:

- Provider implementations
- Event definitions
- Shared domain abstractions
- Shared exceptions

Providers are **not** implemented in this codebase - they are only orchestrated from here.

### Background Tasks

Handles periodic maintenance operations, including:

- Cleanup of inactive clients
- Removal of stale database records

## Technology Stack

- Python 3.13.x
- Async PostgreSQL driver (asyncpg)
- SQLAlchemy (async ORM)
- Alembic (database migrations)
- Playwright (automation layer)
- uv (recommended package & dependency manager)

## Project Structure

- `agent/`
    - Contains the core agent logic:
	    - Prompts
	    - Tools
	    - Agent graph implementation

- `database/`
    - Contains:
	    - ORM models
	    - Repository classes
	    - Utility modules
	    - Async PostgreSQL engine configuration

- `server/`
    - Contains REST server implementation and endpoint definitions.

- `backend_utils/`
    - General-purpose utilities, including:
        - Custom exceptions
	    - Event management utilities
	    - Database security utilities (encryption of sensitive data)
	    - Computer-use related helpers
	    - Context representation classes and ADTs

- `background/`
    - Database cleanup logic.

- `config.py`
    - Centralized environment and `.env` variable access

## Setup

Note that all code snippets use `bash` commands (suitable for Linux, macOS, Git Bash, or WSL on Windows). If you're using Windows (e.g., PowerShell or CMD), refer to the equivalent commands for your shell.

### Using uv (Recommended)

```bash
uv sync
source .venv/bin/activate
```

### Using pip (Alternative - not recommended)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

**Note**: `pip` is significantly slower and requires you to use exactly Python 3.13.x when creating the venv.

### Chromium Installation

Before installing [Chromium](https://www.chromium.org/chromium-projects/) via [Playwright](https://playwright.dev), make sure the virtual environment is active. Then install the browser:

```bash
python -m playwright install chromium
```

## Database Setup

### Initialize Migrations Folder (only needed once)

```bash
cp -r alembic_template/alembic/ alembic/
cp alembic_template/alembic.ini alembic.ini
```

### Create Initial Migration and Tables 

```bash
python -m alembic revision --autogenerate -m "initial schema"
python -m alembic upgrade head
```

### Later Schema Changes (example)

```bash
# 1. Generate new migration after changing models
python -m alembic revision --autogenerate -m "added new column"

# 2. Apply it
python -m alembic upgrade head
```

## Environment Configuration

Copy the example file:

```bash
cp .env.example .env
```

Edit `.env` following the comments inside the file.

Make sure the **most important** variables are set:

- Get your **Gemini API key** from https://aistudio.google.com
- Generate a secure **encryption key** for sensitive data:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output and paste it as `SECRET_KEY=...` in your `.env` file.

## Running the Backend

Make sure you are in the `src` directory.

### Development / debugging mode (mainly for Playwright testing)

```bash
python -m backend.agent.main_agent
```

**Note**: This mode was created mainly for testing Playwright automation and may not work fully with the complete system flow (UI + DB + events).

### Production / normal mode (recommended)

```bash
python -m backend
```

This starts the full server with REST API, database, background tasks, etc.

## Extending the Backend

### Adding a New Provider

1. Go to the `shared` package
2. Create the new provider inside `src/shared/provider/`
3. Inherit from `BaseProvider`
4. Implement the required abstract methods

### Adding a New REST Endpoint

1. Add the route/handler in `src/server/`
2. Update the frontend (or another client) to interact with the new endpoint as required

### Adding a New Database Model

1. Create the new model in `src/database/models/`
2. (If needed) Create a matching repository in `src/database/repositories/`
3. Generate and apply new migration:

```bash
python -m alembic revision --autogenerate -m "added XYZ model"
python -m alembic upgrade head
```