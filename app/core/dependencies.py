# app/core/dependencies.py
"""Simplified dependency injection using unified query engine"""

from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Generator
from .database import get_dw_session, get_config_session
from app.shared.query_engine import QueryEngine

# Database session dependencies
def get_dw_db() -> Generator[Session, None, None]:
    """Get data warehouse database session"""
    yield from get_dw_session()

def get_config_db() -> Generator[Session, None, None]:
    """Get config database session"""
    yield from get_config_session()

# Unified query engine dependency
def get_query_engine(
    dw_db: Session = Depends(get_dw_db),
    config_db: Session = Depends(get_config_db)
) -> QueryEngine:
    """Get unified query engine with both database sessions"""
    return QueryEngine(dw_db, config_db)

# Service dependencies for config-only operations
def get_config_only_db() -> Generator[Session, None, None]:
    """Get config database session for operations that don't need data warehouse"""
    yield from get_config_session()