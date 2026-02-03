
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.credential import Credential
from backend.database.actions.client_touch import touch_client
from backend.backend_utils.security.db_security import encrypt, decrypt


async def upsert_credentials(
        db: AsyncSession,
        session_id: str,
        store: str,
        username: str,
        password: str
    ) -> None:
    """"""

    stmt = (
        select(Credential)
        .where(
            Credential.session_id == session_id,
            Credential.store == store
        )
    )

    result = await db.execute(stmt)
    cred = result.scalar_one_or_none()

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
            password=enc_password
        )

        db.add(cred)

    await touch_client(db, session_id)
    await db.commit()


async def get_credentials(
        db: AsyncSession,
        session_id: str,
        store: str
    ) -> dict[str, str] | None:
    """"""

    stmt = (
        select(Credential)
        .where(
            Credential.session_id == session_id,
            Credential.store == store
        )
    )

    result = await db.execute(stmt)
    cred = result.scalar_one_or_none()

    if not cred:
        return None

    return {
        "username": decrypt(cred.username),
        "password": decrypt(cred.password)
    }