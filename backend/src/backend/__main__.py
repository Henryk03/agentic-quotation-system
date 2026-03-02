import asyncio
import logging
import sys

from backend.config import settings
from backend.server.rest_server import start_server


logging.basicConfig(
    level = settings.LOG_LEVEL,
    format = "%(levelname)s | %(asctime)s | %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("agent-server")


async def main() -> int:
    """
    Validate configuration and start the asynchronous backend server.

    Reads settings from environment variables, validates them, and 
    starts the FastAPI server using host and port from the .env file.

    Returns
    -------
    int
        Exit code. 0 if successful, 1 if configuration errors or server
        startup errors occur.
    """

    logger.info("initializing Agentic Backend Server...")

    is_valid: bool = False
    errors: list[str] = []

    is_valid, errors = settings.validate()

    if not is_valid:
        logger.error("configuration errors found:")

        for err in errors:
            logger.error(f"   - {err}")

        logger.info("please edit your .env file to fix these issues.")
        return 1

    logger.info("configuration validated and loaded")
    logger.info(
        f"starting server on {settings.HOST}:{settings.PORT} "
        f"(Headless={settings.HEADLESS})"
    )

    try:
        await start_server(host = settings.HOST, port = settings.PORT)

    except Exception as e:
        logger.exception(f"server error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("shutdown requested by user")
        exit_code = 0

    sys.exit(exit_code)