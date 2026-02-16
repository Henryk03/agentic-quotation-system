
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)

from backend.config import settings


DATABASE_URL: str | None = settings.DATABASE_URL

if DATABASE_URL:
    engine = create_async_engine(
        DATABASE_URL, 
        echo = False
    )
    AsyncSessionLocal = async_sessionmaker(
        bind = engine,
        class_ = AsyncSession,
        expire_on_commit = False
    )