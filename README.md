
# Agentic Quotation System

The Agentic Quotation System is designed to simplify and accelerate the quotation process for professionals while also supporting commercial retailers and casual users who want to compare product prices across different stores.

The system leverages an agent-based architecture to automate product lookup, price retrieval, and quotation preparation, reducing manual effort and improving efficiency.

## Project Structure

The project is organized as a modular system composed of three independent but coordinated codebases:

- **backend** 
    - REST server
    - Agent orchestration logic
    - Database layer
- **frontend** 
    - User interface
- **shared** 
    - Shared domain models
    - Events
    - Provider implementations
    - General-purpose utilities

All codebases are fully documented, type-annotated, and structured to maximize maintainability, clarity, and extensibility


## Architectural Overview

- **backend**
    - Exposes REST endpoints, orchestrates agent execution, and persists essential data in the database.
- **frontend**
    - Communicates with the backend via REST and provides the user interface.
- **shared** 
    - Contains:
        - Events exchanged between UI and server
        - Playwright utilities
        - Store/provider implementations
        - Shared exceptions and domain abstractions

This separation enforces clear responsibility boundaries, improves reusability, and enables independent evolution of each component.

## Requirements

- python 3.13.x
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Google Chrome with the [uBlock Origin](https://ublockorigin.com/it) extension enabled

For proper functionality of [Gemini Computer Use](https://ai.google.dev/gemini-api/docs/computer-use), specific filter blocks must be enabled via the uBlock Origin Lite dashboard under the “**Filter lists**” section:

![ublock_settings](/assets/screenshots/uBlock_settings.png)

## Quickstart

### 1. Clone the Repository

```bash
git clone https://github.com/Henryk03/agentic-quotation-system.git
cd agentic-quotation-system
```


### 2. Configure the Database

Before setting up the backend, create a database with a name of your choice, provided that an asynchronous Python driver is available (for example, [asyncpg](https://github.com/MagicStack/asyncpg) for PostgreSQL).

Example for PostgreSQL:

```sql
CREATE DATABASE agent_chat_db;
```

### 3. Backend Setup

After creating and configuring the database, move into the `backend` directory and follow the instructions provided in:

```bash
backend/README.md
```

### 4. Frontend Setup

Once the backend is running, move into the `frontend` directory and follow the instructions provided in:

```bash
frontend/README.md
```

## License

**Agentic Quotation System** is developed and distributed under the MIT license.