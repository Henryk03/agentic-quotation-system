
import os
from dotenv import load_dotenv
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = BACKEND_ROOT / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class Settings:
    """
    Application configuration loaded from environment 
    variables.

    The configuration values are retrieved from the operating 
    system environment. If a `.env` file exists at the backend 
    root directory, it is automatically loaded before reading 
    variables.

    Attributes
    ----------
    HOST : str
        Host address used by the backend server. Defaults to `"0.0.0.0"`.

    PORT : int
        Port used by the backend server. Defaults to `8080`.

    STREAMLIT_HOST : str or None
        Host address used by the Streamlit frontend.

    STREAMLIT_PORT : str or None
        Port used by the Streamlit frontend.

    Notes
    -----
    This class does not perform validation beyond basic type casting.
    Environment variables are expected to be correctly formatted.
    """
    
    def __init__(self):
        # Server Connection
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8080"))
        
        # Streamlit Configuration
        self.STREAMLIT_HOST=os.getenv("STREAMLIT_HOST")
        self.STREAMLIT_PORT=os.getenv("STREAMLIT_PORT")


settings = Settings()