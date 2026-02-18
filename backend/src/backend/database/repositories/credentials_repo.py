
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.backend_utils.security.db_security import decrypt, encrypt
from backend.database.actions.client_touch import touch_client
from backend.database.models.credential import Credential


class CredentialsRepository:
    """"""
    

    @staticmethod
    async def upsert_credentials(
            db: AsyncSession,
            client_id: str,
            store: str,
            username: str,
            password: str
        ) -> None:
        """"""

        stmt = (
            select(Credential)
            .where(
                Credential.client_id == client_id,
                Credential.store == store
            )
        )

        result = await db.execute(stmt)
        cred: Credential | None = result.scalar_one_or_none()

        enc_username: str = encrypt(username)
        enc_password: str = encrypt(password)

        if cred:
            cred.username = enc_username
            cred.password = enc_password

        else:
            cred = Credential(
                client_id=client_id,
                store=store,
                username=enc_username,
                password=enc_password
            )

            db.add(cred)

        await touch_client(db, client_id)
        await db.commit()


    @staticmethod
    async def get_credentials(
            db: AsyncSession,
            client_id: str,
            store: str
        ) -> tuple[str | None, str | None]:
        """"""

        stmt = (
            select(Credential)
            .where(
                Credential.client_id == client_id,
                Credential.store == store
            )
        )

        result = await db.execute(stmt)
        cred = result.scalar_one_or_none()

        if not cred:
            return (None, None)

        return (
            decrypt(cred.username),
            decrypt(cred.password)
        )