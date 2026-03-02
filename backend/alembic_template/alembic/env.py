
import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from dotenv import load_dotenv


# =============================
#       Python Path Fix
# =============================

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
SRC_PATH: Path = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_PATH))


# =============================
#           Imports
# =============================

load_dotenv()

from backend.config import settings
from backend.database.base import Base
from backend.database.models import *


# =============================
#        Alembic Config
# =============================

config = context.config

config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL,
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# =============================
#          Migrations
# =============================

def run_migrations_offline() -> None:
    """
    Run Alembic migrations in 'offline' mode.

    This generates SQL statements without connecting to 
    the database. Useful for producing migration scripts 
    that can be reviewed or applied manually.

    Returns
    -------
    None
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(
        connection: Connection
    ) -> None:
    """
    Execute migrations on a given synchronous 
    SQLAlchemy connection.

    Configures the Alembic context to use the provided 
    connection and runs all pending migrations.

    Parameters
    ----------
    connection : Connection
        A synchronous SQLAlchemy connection object to use 
        for migrations.

    Returns
    -------
    None
    """

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run Alembic migrations in 'online' asynchronous mode.

    Establishes an asynchronous engine connection to the 
    database and runs migrations in a transaction.

    Returns
    -------
    None
    """
    
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run Alembic migrations in 'online' mode using asyncio.

    This function runs the asynchronous migration function 
    using `asyncio.run`.

    Returns
    -------
    None
    """
    
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
    
else:
    run_migrations_online()