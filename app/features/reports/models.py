# app/features/reports/models.py
"""Updated models with cycle_code moved to execution logs"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, SmallInteger
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.core.database import ConfigBase as Base

class Report(Base):
    """Report templates - reusable report configurations (no cycle_code)"""
    __tablename__ = "reports"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    aggregation_level: Mapped[str] = mapped_column(String(20), nullable=False)  # 'deal' or 'tranche'
    # cycle_code removed - now specified at execution time
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Relationships
    report_deals = relationship("ReportDeal", back_populates="report", cascade="all, delete-orphan")
    report_tranches = relationship("ReportTranche", back_populates="report", cascade="all, delete-orphan")
    report_calculations = relationship("ReportCalculation", back_populates="report", cascade="all, delete-orphan")
    execution_logs = relationship("ReportExecutionLog", back_populates="report")

class ReportDeal(Base):
    """Many-to-many relationship between reports and deals"""
    __tablename__ = "report_deals"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    deal_number: Mapped[int] = mapped_column(Integer, nullable=False)  # References Deal.dl_nbr in DW
    
    # Relationships
    report = relationship("Report", back_populates="report_deals")

class ReportTranche(Base):
    """Many-to-many relationship between reports and tranches"""
    __tablename__ = "report_tranches"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    deal_number: Mapped[int] = mapped_column(Integer, nullable=False)  # References Deal.dl_nbr
    tranche_id: Mapped[str] = mapped_column(String(15), nullable=False)  # References Tranche.tr_id
    
    # Relationships
    report = relationship("Report", back_populates="report_tranches")

class ReportCalculation(Base):
    """Many-to-many relationship between reports and calculations"""
    __tablename__ = "report_calculations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    calculation_id: Mapped[int] = mapped_column(ForeignKey("calculations.id"), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    display_name: Mapped[str] = mapped_column(String(100), nullable=True)  # Override calculation name
    
    # Relationships
    report = relationship("Report", back_populates="report_calculations")

class ReportExecutionLog(Base):
    """Log of report executions - now includes cycle_code"""
    __tablename__ = "report_execution_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    cycle_code: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # Moved here from Report
    executed_by: Mapped[str] = mapped_column(String(100), nullable=True)
    execution_time_ms: Mapped[float] = mapped_column(nullable=True)
    row_count: Mapped[int] = mapped_column(nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    executed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    report = relationship("Report", back_populates="execution_logs")
