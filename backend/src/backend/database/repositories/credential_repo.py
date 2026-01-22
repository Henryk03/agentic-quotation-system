
from sqlalchemy.orm import Session

from backend.database.models.credential import Credential
from backend.backend_utils.security.db_security import encrypt, decrypt


def upsert_credentials(
        db: Session,
        session_id: str,
        store: str,
        username: str,
        password: str
    ) -> None:
    """"""

    cred = (
        db.query(Credential)
        .filter_by(session_id=session_id, store=store)
        .first()
    )

    enc_username = encrypt(username)
    enc_password = encrypt(password)

    if cred:
        cred.username = enc_username
        cred.password = enc_password

    else:
        cred = Credential(
            session_id=session_id,
            store=store,
            username=enc_username,
            password_encrypted=enc_password
        )

        db.add(cred)

    db.commit()


def get_credentials(
        db: Session,
        session_id: str,
        store: str
    ) -> dict[str, str] | None:
    """"""

    cred = (
        db.query(Credential)
        .filter_by(session_id=session_id, store=store)
        .first()
    )

    if not cred:
        return None

    return {
        "username": decrypt(cred.username),
        "password": decrypt(cred.password)
    }