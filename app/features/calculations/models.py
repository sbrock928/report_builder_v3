# app/features/calculations/models.py
"""Database models for calculations feature"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.core.database import ConfigBase as Base

class Calculation(Base):
    """Stored calculation definitions"""
    __tablename__ = "calculations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    formula: Mapped[str] = mapped_column(Text, nullable=False)
    aggregation_method: Mapped[str] = mapped_column(String(50), nullable=False)
    group_level: Mapped[str] = mapped_column(String(20), nullable=False)  # 'deal' or 'tranche'
    source_tables: Mapped[list] = mapped_column(JSON, nullable=False)  # List of table names
    dependencies: Mapped[list] = mapped_column(JSON, nullable=True, default=[])  # List of calculation names
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Relationships
    report_calculations = relationship("ReportCalculation", back_populates="calculation")