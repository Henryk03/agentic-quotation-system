
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from playwright.async_api import StorageState

from backend.backend_utils.security.db_security import decrypt, encrypt
from backend.database.actions.client_touch import touch_client
from backend.database.models.login_context import LoginContext


class LoginContextRepository:
    """"""


    @staticmethod
    async def upsert_browser_context(
            db: AsyncSession,
            client_id: str,
            store: str,
            state: StorageState
        ) -> None:
        """"""

        stmt = (
            select(LoginContext)
            .where(
                LoginContext.client_id == client_id,
                LoginContext.store == store
            )
        )

        result = await db.execute(stmt)
        context = result.scalar_one_or_none()

        string_state: str = json.dumps(state)
        enc_state: str = encrypt(string_state)

        if context:
            context.context_data = enc_state
            context.locked_until = None
            context.last_error_message = None
            context.last_error_at = None

        else:
            context = LoginContext(
                client_id = client_id,
                store = store,
                context_data = enc_state,
                attempts_history = [],
                locked_until = None,
                last_error_message = None,
                last_error_at = None
            )

            db.add(context)

        await touch_client(db, client_id)
        await db.commit()


    @staticmethod
    async def get_browser_context(
            db: AsyncSession,
            client_id: str,
            store: str
        ) -> StorageState | None:
        """"""

        stmt = (
            select(LoginContext)
            .where(
                LoginContext.client_id == client_id,
                LoginContext.store == store
            )
        )

        result = await db.execute(stmt)
        context = result.scalar_one_or_none()

        if not context or not context.context_data:
            return None

        dec_state: str = decrypt(context.context_data).strip()

        try:
            return StorageState(json.loads(dec_state))
        
        except (json.JSONDecodeError, TypeError):
            return None


    @staticmethod
    async def add_login_attempt(
            db: AsyncSession,
            client_id: str,
            store: str,
            status: str,
            reason: str | None = None,
            max_attempts: int = 3,
            cooldown_minutes: int = 15
        ) -> None:
        """"""

        stmt = (
            select(LoginContext)
            .where(
                LoginContext.client_id == client_id,
                LoginContext.store == store
            )
        )

        result = await db.execute(stmt)
        context = result.scalar_one_or_none()

        now: datetime = datetime.now(timezone.utc)

        new_attempt: dict[str, Any] = {
            "timestamp": now.isoformat(),
            "status": status,
            "reason": reason
        }

        if context:
            if context.attempts_history is None:
                context.attempts_history = []

            context.attempts_history.append(new_attempt)

        else:
            context = LoginContext(
                client_id = client_id,
                store = store,
                context_data = encrypt(""),
                attempts_history = [new_attempt],
                locked_until = None,
                last_error_message = None,
                last_error_at = None
            )

            db.add(context)

        if status == "success":
            context.locked_until = None
            context.last_error_message = None
            context.last_error_at = None

        elif status == "failed":
            context.last_error_message = reason
            context.last_error_at = now

            failure_count: int = (
                await LoginContextRepository.count_recent_failures(
                    db,
                    client_id,
                    store,
                    hours = 24
                )
            )

            if failure_count >= max_attempts:
                context.locked_until = now + timedelta(
                    minutes = cooldown_minutes
                )

        await touch_client(db, client_id)
        await db.commit()


    @staticmethod
    async def count_recent_failures(
            db: AsyncSession,
            client_id: str,
            store: str,
            hours: int = 24
        ) -> int:
        """"""

        stmt = (
            select(LoginContext)
            .where(
                LoginContext.client_id == client_id,
                LoginContext.store == store
            )
        )

        result = await db.execute(stmt)
        context = result.scalar_one_or_none()

        if not context or not context.attempts_history:
            return 0

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours = hours)

        count = 0

        for attempt in context.attempts_history:
            if attempt.get("status") != "failed":
                continue

            attempt_time = datetime.fromisoformat(attempt["timestamp"])

            if attempt_time >= cutoff_time:
                count += 1

        return count


    @staticmethod
    async def can_attempt_login(
            db: AsyncSession,
            client_id: str,
            store: str
        ) -> tuple[bool, str | None, int | None]:
        """"""

        stmt = (
            select(LoginContext)
            .where(
                LoginContext.client_id == client_id,
                LoginContext.store == store
            )
        )

        result = await db.execute(stmt)
        context = result.scalar_one_or_none()

        if not context:
            return True, None, None

        now = datetime.now(timezone.utc)

        if context.locked_until and context.locked_until > now:
            minutes_left = int(
                (context.locked_until - now).total_seconds() / 60
            ) + 1

            return (
                False,
                f"Too many failed attempts. Try again in {minutes_left} minutes.",
                minutes_left
            )

        return True, None, None