# app/features/reports/repository.py
"""Data access layer for reports operations"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any
from .models import ReportExecutionLog

class ReportRepository:
    """Repository for report-related data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_execution(
        self,
        report_name: str,
        executed_by: str,
        execution_time_ms: float,
        row_count: int,
        parameters: Dict[str, Any],
        success: bool,
        error_message: str = None
    ) -> ReportExecutionLog:
        """Log report execution to database"""
        log_entry = ReportExecutionLog(
            report_name=report_name,
            executed_by=executed_by,
            execution_time_ms=execution_time_ms,
            row_count=row_count,
            parameters=parameters,
            success=success,
            error_message=error_message
        )
        
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        return log_entry