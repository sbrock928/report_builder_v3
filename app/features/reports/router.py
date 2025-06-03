# app/features/reports/router.py
"""API endpoints for report generation"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_dw_db, get_config_db
from app.core.exceptions import ReportGenerationError
from .service import ReportService
from .schemas import ReportRequest, ReportResponse

router = APIRouter()

def get_report_service(
    dw_db: Session = Depends(get_dw_db),
    config_db: Session = Depends(get_config_db)
) -> ReportService:
    """Get report service with database sessions"""
    return ReportService(dw_db=dw_db, config_db=config_db)

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    service: ReportService = Depends(get_report_service)
):
    """Generate a report with the specified calculations and filters"""
    try:
        return await service.generate_report(request)
    except ReportGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/preview-sql")
async def preview_report_sql(
    request: ReportRequest,
    service: ReportService = Depends(get_report_service)
):
    """Preview the SQL that would be generated for a complete report"""
    try:
        preview = await service.preview_report_sql(request)
        return preview
    except ReportGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))