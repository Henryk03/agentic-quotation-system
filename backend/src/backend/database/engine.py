
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import settings


DATABASE_URL: str | None = settings.DATABASE_URL

if DATABASE_URL:
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)