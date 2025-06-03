# app/features/reports/repository.py
"""Repository for refactored reports operations"""

from sqlalchemy.orm import Session
from typing import List, Optional
from .models import Report, ReportDeal, ReportTranche, ReportCalculation, ReportExecutionLog

class ReportRepository:
    """Repository for report-related data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_active_reports(self) -> List[Report]:
        """Get all active report templates"""
        return self.db.query(Report).filter(Report.is_active == True).order_by(Report.created_at.desc()).all()
    
    def get_report_by_id(self, report_id: int) -> Optional[Report]:
        """Get report template by ID"""
        return self.db.query(Report).filter(
            Report.id == report_id,
            Report.is_active == True
        ).first()
    
    def get_report_by_name(self, name: str) -> Optional[Report]:
        """Get report template by name"""
        return self.db.query(Report).filter(
            Report.name == name,
            Report.is_active == True
        ).first()
    
    def create_report(self, report: Report) -> Report:
        """Create a new report template"""
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report
    
    def update_report(self, report: Report) -> Report:
        """Update an existing report template"""
        self.db.commit()
        self.db.refresh(report)
        return report
    
    def delete_report(self, report: Report) -> Report:
        """Soft delete a report template"""
        report.is_active = False
        self.db.commit()
        return report
    
    def get_execution_logs(self, report_id: int, limit: int = 50) -> List[ReportExecutionLog]:
        """Get recent execution logs for a report"""
        return self.db.query(ReportExecutionLog)\
            .filter(ReportExecutionLog.report_id == report_id)\
            .order_by(ReportExecutionLog.executed_at.desc())\
            .limit(limit).all()