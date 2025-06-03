# app/features/reports/router.py
"""Updated API endpoints with cycle_code required for execution"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.dependencies import get_dw_db, get_config_db
from app.core.exceptions import ReportGenerationError
from .service import ReportService
from .schemas import (
    ReportCreateRequest, ReportUpdateRequest, ReportExecuteRequest,
    ReportResponse, ReportTemplateResponse, ReportTemplateDetailResponse
)

router = APIRouter()

def get_report_service(
    dw_db: Session = Depends(get_dw_db),
    config_db: Session = Depends(get_config_db)
) -> ReportService:
    """Get report service with database sessions"""
    return ReportService(dw_db=dw_db, config_db=config_db)

@router.post("/templates", response_model=ReportTemplateDetailResponse, status_code=201)
async def create_report_template(
    request: ReportCreateRequest,
    service: ReportService = Depends(get_report_service)
):
    """Create a new report template (no cycle_code required)"""
    try:
        return await service.create_report_template(request)
    except ReportGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/templates", response_model=List[ReportTemplateResponse])
async def get_report_templates(
    service: ReportService = Depends(get_report_service)
):
    """Get list of all report templates with execution history"""
    return await service.get_report_templates()

@router.get("/templates/{report_id}", response_model=ReportTemplateDetailResponse)
async def get_report_template_detail(
    report_id: int,
    service: ReportService = Depends(get_report_service)
):
    """Get detailed report template configuration with recent executions"""
    try:
        return await service.get_report_template_detail(report_id)
    except ReportGenerationError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/templates/{report_id}/preview-sql")
async def preview_report_sql(
    report_id: int,
    service: ReportService = Depends(get_report_service),
    cycle_code: int = Query(202404, description="Sample cycle code for SQL preview")
):
    """Preview the SQL that would be generated for this report template using the same ORM logic as execution"""
    try:
        return await service.preview_report_sql(report_id, cycle_code)
    except ReportGenerationError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/templates/{report_id}", response_model=ReportTemplateDetailResponse)
async def update_report_template(
    report_id: int,
    request: ReportUpdateRequest,
    service: ReportService = Depends(get_report_service)
):
    """Update an existing report template (no cycle_code)"""
    try:
        return await service.update_report_template(report_id, request)
    except ReportGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/templates/{report_id}")
async def delete_report_template(
    report_id: int,
    service: ReportService = Depends(get_report_service)
):
    """Delete a report template"""
    try:
        return await service.delete_report_template(report_id)
    except ReportGenerationError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/templates/{report_id}/execute", response_model=ReportResponse)
async def execute_report(
    report_id: int,
    request: ReportExecuteRequest,  # cycle_code is now required in the request body
    service: ReportService = Depends(get_report_service)
):
    """Execute a report template with specified cycle_code"""
    try:
        return await service.execute_report(report_id, request)
    except ReportGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/templates/{report_id}/logs")
async def get_report_execution_logs(
    report_id: int,
    service: ReportService = Depends(get_report_service),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of logs to return")
):
    """Get execution logs for a report template (now includes cycle_code)"""
    try:
        return await service.get_execution_logs(report_id, limit)
    except ReportGenerationError as e:
        raise HTTPException(status_code=404, detail=str(e))