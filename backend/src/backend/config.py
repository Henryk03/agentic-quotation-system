
import os
from dotenv import load_dotenv
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = BACKEND_ROOT / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class Settings:
    """"""
    
    def __init__(self):
        # Development and logs
        self.CLI_MODE: bool = os.getenv("CLI_MODE", "false").lower() == "true"
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Google Gemini API
        self.GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
        
        # Server Configuration
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8080"))
        
        # Database Configuration
        self.DATABASE_URL: str = os.getenv(
            "DATABASE_URL", 
            "protocol://user:password@host:port/db_name"
        )
        
        # Playwright / Browser
        self.HEADLESS: bool = os.getenv("HEADLESS", "true").lower() == "true"

        # Login mode
        self.AUTO_LOGIN_ONLY: bool = (
            os.getenv("AUTO_LOGIN_ONLY", "true").lower() == "true"
        )

        # Secret key
        self.SECRET_KEY: str | None = os.getenv("SECRET_KEY", None)


    def validate(self) -> tuple[bool, list[str]]:
        """"""

        errors: list[str] = []

        if not self.GOOGLE_API_KEY or self.GOOGLE_API_KEY == "your_api_key_here":
            errors.append("GOOGLE_API_KEY is missing or set to default.")
        
        if "protocol://" in self.DATABASE_URL:
            if not self.CLI_MODE:
                errors.append("DATABASE_URL is not configured.")
            
        return len(errors) == 0, errors


settings = Settings()