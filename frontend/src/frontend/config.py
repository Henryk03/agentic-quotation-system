

import os
from pathlib import Path
from dotenv import load_dotenv


BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = BACKEND_ROOT / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class Settings:
    """"""
    
    def __init__(self):
        # Server Connection
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8080"))
        
        # Streamlit Configuration
        self.STREAMLIT_HOST=os.getenv("STREAMLIT_HOST")
        self.STREAMLIT_PORT=os.getenv("STREAMLIT_PORT")


settings = Settings()