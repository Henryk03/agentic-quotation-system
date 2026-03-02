
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    Inherits from `DeclarativeBase` to provide common 
    ORM functionality and metadata for all database models.
    """
    
    pass