
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from playwright.async_api import StorageState

from backend.backend_utils.security.db_security import decrypt, encrypt
from backend.database.actions.client_touch import touch_client
from backend.database.models.login_attempt import LoginAttempt
from backend.database.models.login_context import LoginContext


class LoginContextRepository:
    """"""


    @staticmethod
    async def get_or_create_context(
            db: AsyncSession,
            client_id: str,
            store: str
        ) -> LoginContext:
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

        if context:
            return context

        context = LoginContext(
            client_id=client_id,
            store=store
        )

        db.add(context)
        await db.commit()

        return context


    @staticmethod
    async def upsert_context(
            db: AsyncSession,
            client_id: str,
            store: str,
            state: StorageState
        ) -> None:
        """"""

        context: LoginContext = (
            await LoginContextRepository.get_or_create_context(
                db,
                client_id,
                store
            )
        )

        string_state: str = json.dumps(state)
        enc_state: str = encrypt(string_state)

        context.context_data = enc_state
        context.locked_until = None
        context.last_error_message = None
        context.last_error_at = None

        await touch_client(db, client_id)
        await db.commit()


    @staticmethod
    async def get_storage_state(
            db: AsyncSession,
            client_id: str,
            store: str
        ) -> StorageState | None:
        """"""

        context: LoginContext = (
            await LoginContextRepository.get_or_create_context(
                db,
                client_id,
                store
            )
        )

        if not context.context_data:
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
            success: bool,
            reason: str | None = None
        ) -> None:
        """"""

        context: LoginContext = (
            await LoginContextRepository.get_or_create_context(
                db,
                client_id,
                store
            )
        )

        attempt = LoginAttempt(
            client_id = client_id,
            store = store,
            success = success,
            reason = reason
        )

        db.add(attempt)

        if success:
            context.current_attemps = 0
            context.locked_until = None
            context.last_error_message = None
            context.last_error_at = None

        else:
            now: datetime = datetime.now(timezone.utc)

            context.current_attemps += 1
            context.last_error_message = reason
            context.last_error_at = now

            if context.current_attemps >= context.max_attempts:
                context.locked_until = now + timedelta(
                    seconds = context.cooldown_seconds
                )
                context.current_attemps = 0

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

        cutoff: datetime = (
            datetime.now(timezone.utc) - timedelta(hours = hours)
        )

        stmt = (
            select(LoginAttempt)
            .where(
                LoginAttempt.client_id == client_id,
                LoginAttempt.store == store,
                LoginAttempt.success.is_(False),
                LoginAttempt.created_at >= cutoff
            )
        )

        result = await db.execute(stmt)
        return len(result.scalars().all())


    @staticmethod
    async def can_attempt_login(
            db: AsyncSession,
            client_id: str,
            store: str
        ) -> tuple[bool, str | None, int | None]:
        """"""

        context: LoginContext = (
            await LoginContextRepository.get_or_create_context(
                db,
                client_id,
                store
            )
        )

        now = datetime.now(timezone.utc)

        if context.locked_until and context.locked_until > now:
            minutes_left = int(
                ((context.locked_until - now).total_seconds() + 59) // 60
            )

            return (
                False,
                f"Too many failed attempts. Try again in {minutes_left} minutes.",
                minutes_left
            )
        
        if context.locked_until and context.locked_until <= now:
            context.locked_until = None
            context.current_attemps = 0

            await db.commit()

        return True, None, None