
import json
from sqlalchemy.orm import Session

from backend.database.models.browser_context import BrowserContext
from backend.backend_utils.security.db_security import encrypt, decrypt


def upsert_browser_context(
        db: Session,
        session_id: str,
        store: str,
        state: dict
    ) -> None:
    """"""
    
    context = (
        db.query(BrowserContext)
        .filter_by(session_id=session_id, store=store)
        .first()
    )

    json_state = json.dumps(state)
    enc_state = encrypt(json_state)

    if context:
        context.state = enc_state

    else:
        context = BrowserContext(
            session_id=session_id,
            store=store,
            state=enc_state
        )

        db.add(context)

    db.commit()


def get_browser_context(
        db: Session,
        session_id: str,
        store: str
    ) -> dict | None:
    """"""

    context = (
        db.query(BrowserContext)
        .filter_by(session_id=session_id, store=store)
        .first()
    )

    if not context:
        return None

    dec_json = decrypt(context.state)
    
    try:
        return json.loads(dec_json)
    
    except (json.JSONDecodeError, TypeError):
        return None