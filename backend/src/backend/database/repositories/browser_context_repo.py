
import json
from sqlalchemy.orm import Session

from playwright.async_api import StorageState

from backend.database.models.browser_context import BrowserContext
from backend.backend_utils.security.db_security import encrypt, decrypt


def upsert_browser_context(
        db: Session,
        session_id: str,
        store: str,
        state: StorageState | str,
        fail_reason: str | None
    ) -> None:
    """"""
    
    context = (
        db.query(BrowserContext)
        .filter_by(session_id=session_id, store=store)
        .first()
    )

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

    db.commit()


def get_browser_context(
        db: Session,
        session_id: str,
        store: str
    ) -> tuple[StorageState | str | None, str | None]:
    """"""

    context: BrowserContext | None = (
        db.query(BrowserContext)
        .filter_by(session_id=session_id, store=store)
        .first()
    )

    if not context:
        return None, None

    dec_state: str = decrypt(context.state).strip()

    if not (dec_state.startswith('{') or dec_state.startswith('[')):
        return dec_state, context.fail_reason

    try:
        return json.loads(dec_state), context.fail_reason
    
    except (json.JSONDecodeError, TypeError):
        return None, None