# app/config/models.py
"""Database models for the configuration database (calculations, reports, etc.)"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
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

class ReportTemplate(Base):
    """Saved report templates/configurations"""
    __tablename__ = "report_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    aggregation_level: Mapped[str] = mapped_column(String(20), nullable=False)  # 'deal' or 'tranche'
    default_filters: Mapped[dict] = mapped_column(JSON, nullable=True, default={})  # Default filter values
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Relationships
    calculations = relationship("ReportCalculation", back_populates="report_template")

class ReportCalculation(Base):
    """Many-to-many relationship between reports and calculations"""
    __tablename__ = "report_calculations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_template_id: Mapped[int] = mapped_column(ForeignKey("report_templates.id"), nullable=False)
    calculation_id: Mapped[int] = mapped_column(ForeignKey("calculations.id"), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    display_name: Mapped[str] = mapped_column(String(100), nullable=True)  # Override calculation name
    
    # Relationships
    report_template = relationship("ReportTemplate", back_populates="calculations")
    calculation = relationship("Calculation", back_populates="report_calculations")

class UserPreference(Base):
    """User-specific preferences and saved filters"""
    __tablename__ = "user_preferences"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    preference_key: Mapped[str] = mapped_column(String(100), nullable=False)
    preference_value: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ReportExecutionLog(Base):
    """Log of report executions for monitoring and debugging"""
    __tablename__ = "report_execution_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_name: Mapped[str] = mapped_column(String(200), nullable=False)
    executed_by: Mapped[str] = mapped_column(String(100), nullable=True)
    execution_time_ms: Mapped[float] = mapped_column(nullable=True)
    row_count: Mapped[int] = mapped_column(nullable=True)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False)  # Report parameters used
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    executed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

