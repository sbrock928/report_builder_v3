# app/reporting/routers/report_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.request_models import ReportRequest, CalculationRequest, AggregationLevel
from ..models.response_models import ReportResponse, CalculationResponse
from ..services.report_service import ReportService
from app.core.database import get_dw_session, get_config_session

router = APIRouter()

def get_report_service(
    dw_db: Session = Depends(get_dw_session),
    config_db: Session = Depends(get_config_session)
) -> ReportService:
    """Get report service with database sessions"""
    return ReportService(dw_db=dw_db, config_db=config_db)

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    service: ReportService = Depends(get_report_service)
):
    """Generate a report with the specified calculations and filters"""
    return await service.generate_report(request)

@router.get("/deals")
async def get_available_deals(
    service: ReportService = Depends(get_report_service)
):
    """Get list of available deals"""
    return await service.get_available_deals()

@router.get("/tranches")
async def get_available_tranches(
    deal_number: Optional[int] = Query(None, description="Filter tranches by deal number"),
    service: ReportService = Depends(get_report_service)
):
    """Get list of available tranches, optionally filtered by deal"""
    return await service.get_available_tranches(deal_number)

@router.get("/cycles")
async def get_available_cycles(
    service: ReportService = Depends(get_report_service)
):
    """Get list of available cycle codes"""
    return await service.get_available_cycles()

@router.get("/calculations", response_model=List[CalculationResponse])
async def get_available_calculations(
    group_level: Optional[str] = Query(None, description="Filter by group level: 'deal', 'tranche'"),
    service: ReportService = Depends(get_report_service)
):
    """Get list of available calculations, optionally filtered by group level"""
    return await service.get_available_calculations(group_level)

@router.post("/preview-sql")
async def preview_report_sql(
    request: ReportRequest,
    service: ReportService = Depends(get_report_service)
):
    """Preview the SQL that would be generated for a complete report"""
    try:
        preview = await service.preview_report_sql(request)
        return preview
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculations/preview-sql")
async def preview_calculation_sql(
    calculation_data: dict,
    service: ReportService = Depends(get_report_service)
):
    """Preview the SQL that would be generated for a calculation"""
    try:
        preview = await service.preview_calculation_sql(calculation_data)
        return preview
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/calculations/{calc_name}/preview-sql")
async def preview_existing_calculation_sql(
    calc_name: str,
    aggregation_level: Optional[str] = Query("deal", description="Aggregation level: 'deal' or 'tranche'"),
    service: ReportService = Depends(get_report_service)
):
    """Preview the SQL for an existing calculation"""
    try:
        # Get the calculation details
        calculations = await service.get_available_calculations()
        calculation = next((calc for calc in calculations if calc.name == calc_name), None)
        
        if not calculation:
            raise HTTPException(status_code=404, detail=f"Calculation '{calc_name}' not found")
        
        # Convert to dict for preview
        calc_dict = {
            'name': calculation.name,
            'formula': calculation.formula,
            'aggregation_method': calculation.aggregation_method,
            'group_level': calculation.group_level,
            'source_tables': calculation.source_tables
        }
        
        # Generate preview with specific aggregation level
        from app.reporting.builders.filter_builder import FilterBuilder
        from app.reporting.builders.report_query_builder import ReportQueryBuilder
        
        filter_builder = FilterBuilder()
        query_builder = ReportQueryBuilder(filter_builder)
        
        sql, params = query_builder.preview_calculation_subquery(
            calc_dict,
            aggregation_level=aggregation_level
        )
        
        return {
            "calculation_name": calc_name,
            "aggregation_level": aggregation_level,
            "sql": sql,
            "sample_parameters": params,
            "group_level": calculation.group_level
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calculations", response_model=CalculationResponse)
async def create_calculation(
    request: CalculationRequest,
    service: ReportService = Depends(get_report_service)
):
    """Create a new calculation"""
    return await service.create_calculation(request)

@router.put("/calculations/{calc_name}", response_model=CalculationResponse)
async def update_calculation(
    calc_name: str,
    request: CalculationRequest,
    service: ReportService = Depends(get_report_service)
):
    """Update an existing calculation"""
    return await service.update_calculation(calc_name, request)

@router.delete("/calculations/{calc_name}")
async def delete_calculation(
    calc_name: str,
    service: ReportService = Depends(get_report_service)
):
    """Delete a calculation"""
    return await service.delete_calculation(calc_name)