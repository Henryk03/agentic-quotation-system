
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from playwright.async_api import StorageState

from backend.backend_utils.security.db_security import (
    decrypt, 
    encrypt
)
from backend.database.actions.client_touch import touch_client
from backend.database.models.login_context import LoginContext


class LoginContextRepository:
    """
    Repository class for managing login contexts for clients 
    and stores.
    """


    @staticmethod
    async def get_or_create_context(
            db: AsyncSession,
            client_id: str,
            store: str
        ) -> LoginContext:
        """
        Retrieve an existing login context for a client and store, 
        or create a new one if it does not exist.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database access.

        client_id : str
            The unique identifier of the client.

        store : str
            The store identifier for which the login context is needed.

        Returns
        -------
        LoginContext
            The existing or newly created login context instance.
        """

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
        """
        Insert or update the encrypted StorageState for a given 
        client and store.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database access.

        client_id : str
            The unique identifier of the client.

        store : str
            The store identifier for which the login context is updated.

        state : StorageState
            The Playwright storage state object to encrypt and save.

        Returns
        -------
        None
        """

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

        await touch_client(db, client_id)
        await db.commit()


    @staticmethod
    async def get_storage_state(
            db: AsyncSession,
            client_id: str,
            store: str
        ) -> StorageState | None:
        """
        Retrieve and decrypt the stored StorageState for a 
        client and store.

        Parameters
        ----------
        db : AsyncSession
            The asynchronous SQLAlchemy session for database 
            access.

        client_id : str
            The unique identifier of the client.

        store : str
            The store identifier for which the storage state 
            is requested.

        Returns
        -------
        StorageState | None
            The decrypted Playwright StorageState if available and valid, 
            otherwise None.
        """

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