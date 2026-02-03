
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from playwright.async_api import StorageState

from backend.database.actions.client_touch import touch_client
from backend.database.models.browser_context import BrowserContext
from backend.backend_utils.security.db_security import encrypt, decrypt


async def upsert_browser_context(
        db: AsyncSession,
        session_id: str,
        store: str,
        state: StorageState | str,
        fail_reason: str | None
    ) -> None:
    """"""
    
    stmt = (
        select(BrowserContext)
        .where(
            BrowserContext.session_id == session_id,
            BrowserContext.store == store
        )
    )

    result = await db.execute(stmt)
    context = result.scalar_one_or_none()

    string_state = json.dumps(state) if isinstance(state, dict) else state
    enc_state = encrypt(string_state)

    if context:
        context.state = enc_state
        context.fail_reason = fail_reason

    else:
        context = BrowserContext(
            session_id=session_id,
            store=store,
            state=enc_state,
            fail_reason=fail_reason
        )

        db.add(context)

    await touch_client(db, session_id)
    await db.commit()


async def get_browser_context(
        db: AsyncSession,
        session_id: str,
        store: str
    ) -> tuple[StorageState | str | None, str | None]:
    """"""

    stmt = (
        select(BrowserContext)
        .where(
            BrowserContext.session_id == session_id,
            BrowserContext.store == store
        )
    )

    result = await db.execute(stmt)
    context = result.scalar_one_or_none() 

    if not context:
        return None, None

    dec_state: str = decrypt(context.state).strip()

    if not (dec_state.startswith('{') or dec_state.startswith('[')):
        return dec_state, context.fail_reason

    try:
        return json.loads(dec_state), context.fail_reason
    
    except (json.JSONDecodeError, TypeError):
        return None, None
    

async def add_login_attempt(
        db: AsyncSession,
        session_id: str,
        store: str,
        status: str,
        reason: str | None = None
    ) -> None:
    """"""
    
    stmt = (
        select(BrowserContext)
        .where(
            BrowserContext.session_id == session_id,
            BrowserContext.store == store
        )
    )
    
    result = await db.execute(stmt)
    context = result.scalar_one_or_none()
    
    new_attempt = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "reason": reason
    }
    
    if context:
        if context.attempts_history is None:
            context.attempts_history = []
        
        context.attempts_history.append(new_attempt)
        
        if status == "failed" and reason:
            context.fail_reason = reason
    
    else:
        context = BrowserContext(
            session_id=session_id,
            store=store,
            state=encrypt(""),
            fail_reason=reason if status == "failed" else None,
            attempts_history=[new_attempt]
        )
        db.add(context)
    
    await touch_client(db, session_id)
    await db.commit()


async def count_recent_failures(
        db: AsyncSession,
        session_id: str,
        store: str,
        hours: int = 24
    ) -> int:
    """"""
    
    stmt = (
        select(BrowserContext)
        .where(
            BrowserContext.session_id == session_id,
            BrowserContext.store == store
        )
    )
    
    result = await db.execute(stmt)
    context = result.scalar_one_or_none()
    
    if not context or not context.attempts_history:
        return 0
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    count = 0
    for attempt in context.attempts_history:
        if attempt.get("status") != "failed":
            continue
        
        attempt_time = datetime.fromisoformat(attempt["timestamp"])

        if attempt_time >= cutoff_time:
            count += 1
    
    return count


async def can_attempt_login(
        db: AsyncSession,
        session_id: str,
        store: str,
        max_attempts: int = 3,
        cooldown_minutes: int = 15
    ) -> tuple[bool, str | None]:
    """"""
    
    failure_count = await count_recent_failures(
        db, 
        session_id, 
        store, 
        hours=24
    )
    
    if failure_count >= max_attempts:
        stmt = (
            select(BrowserContext)
            .where(
                BrowserContext.session_id == session_id,
                BrowserContext.store == store
            )
        )
        
        result = await db.execute(stmt)
        context = result.scalar_one_or_none()
        
        if context and context.attempts_history:
            last_attempt = context.attempts_history[-1]
            last_time = datetime.fromisoformat(last_attempt["timestamp"])
            time_since = datetime.now(timezone.utc) - last_time
            
            if time_since < timedelta(minutes=cooldown_minutes):
                minutes_left = cooldown_minutes - int(time_since.total_seconds() / 60)
                return (
                    False,
                    (
                        f"Too many failed attempts ({failure_count}/{max_attempts}). "
                        f"Try again in {minutes_left} minutes."
                    )
                )
            
            else:
                return True, None
        
        return False, f"Too many failed attempts ({failure_count}/{max_attempts})."
    
    return True, None