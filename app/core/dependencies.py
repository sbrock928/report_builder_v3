# app/core/dependencies.py
"""Dependency injection helpers for FastAPI"""

from sqlalchemy.orm import Session
from typing import Generator
from .database import get_dw_session, get_config_session

# Database session dependencies
def get_dw_db() -> Generator[Session, None, None]:
    """Get data warehouse database session"""
    yield from get_dw_session()

def get_config_db() -> Generator[Session, None, None]:
    """Get config database session"""
    yield from get_config_session()

# Combined session dependency for services that need both
class DatabaseSessions:
    def __init__(self, dw_db: Session, config_db: Session):
        self.dw_db = dw_db
        self.config_db = config_db

def get_database_sessions(
    dw_db: Session = get_dw_db(),
    config_db: Session = get_config_db()
) -> DatabaseSessions:
    """Get both database sessions for services that need access to both"""
    return DatabaseSessions(dw_db, config_db)