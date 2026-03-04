
# Shared

## Overview

The shared package contains domain abstractions and reusable components used by both the backend and the frontend.

It defines the common language of the system: events, providers, exceptions, and shared utilities.

This package is intentionally independent from both backend and frontend to preserve clear architectural boundaries.

## Responsibilities

- Define system events exchanged between UI and server
- Provide provider abstractions and concrete implementations
- Offer Playwright utilities used for automation
- Define shared exceptions
- Provide common domain utilities and enumerations

## Architectural Role

shared acts as the contract layer of the system.

Dependency direction:

```bash
backend -> shared <- frontend
```

- The backend depends on shared to orchestrate providers and handle events.
- The frontend depends on shared to understand available providers and event structures.
- shared must not depend on backend or frontend.

This ensures loose coupling and consistent domain modeling across the system.

## Package Structure

- `events/`
    - Definitions of all domain events exchanged between backend and frontend, including:
        - Chat events
        - Credential events
        - Job status updates
        - Login events
        - Error events
        - Transport abstractions

- `provider/`
    - Contains:
        - `base_provider.py` – abstract provider definition
        - `registry.py` – provider registration system
        - `providers/` – concrete store implementations

- `playwright/`
    - Automation utilities shared across providers:
        - CAPTCHA detection
        - Page utilities
        - Waiting abstractions

- `exceptions/`
    - Shared exception hierarchy.

- `shared_utils/`
    - Common utilities:
        - Enumerations
        - Dictionaries
        - Reusable domain helpers

## Extending the Shared Package

### Adding a New Provider

To add a new provider:

1. Create a new file inside `provider/providers/`
2. Subclass `BaseProvider`
3. Implement all required abstract methods
4. Expose a module-level instance named `provider`

Example:

```python
from shared.provider.base_provider import BaseProvider

class NewStore(BaseProvider):
    ...

provider: BaseProvider = NewStore()
```

5. Import the new module inside `provider/providers/__init__.py`

The `registry.py` module collects provider instances exposed under the provider name.

### Adding a New Event

1.	Define the event class in `events/`
2.	Ensure consistent serialization/deserialization logic
3.	Update consumers (backend and frontend) accordingly

### Adding Shared Utilities

Place reusable, domain-agnostic logic inside `shared_utils/`, avoiding dependencies on backend-specific or UI-specific components.

## Design Principles

- Single source of truth for domain abstractions
- Strict dependency direction
- High cohesion within modules
- Zero coupling to infrastructure layers


## Installation

The `shared` package is normally installed automatically as a dependency of the backend and frontend modules.

## Standalone Installation

#### Using uv (recommended):

```bash
uv add git+https://github.com/Henryk03/agentic-quotation-system.git#subdirectory=shared
```

#### Using pip (alternative):

```bash
python -m pip install git+https://github.com/Henryk03/agentic-quotation-system.git#subdirectory=shared
```