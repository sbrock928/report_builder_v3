# app/features/calculations/router.py
"""API endpoints for calculations management"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.dependencies import get_config_db
from app.core.exceptions import CalculationNotFoundError, CalculationAlreadyExistsError
from .service import CalculationService
from .schemas import CalculationRequest, CalculationResponse

router = APIRouter()

def get_calculation_service(db: Session = Depends(get_config_db)) -> CalculationService:
    """Get calculation service with database session"""
    return CalculationService(db)

@router.get("", response_model=List[CalculationResponse])
async def get_available_calculations(
    group_level: Optional[str] = Query(None, description="Filter by group level: 'deal', 'tranche'"),
    service: CalculationService = Depends(get_calculation_service)
):
    """Get list of available calculations, optionally filtered by group level"""
    return await service.get_available_calculations(group_level)

@router.post("", response_model=CalculationResponse)
async def create_calculation(
    request: CalculationRequest,
    service: CalculationService = Depends(get_calculation_service)
):
    """Create a new calculation"""
    try:
        return await service.create_calculation(request)
    except CalculationAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.put("/{calc_name}", response_model=CalculationResponse)
async def update_calculation(
    calc_name: str,
    request: CalculationRequest,
    service: CalculationService = Depends(get_calculation_service)
):
    """Update an existing calculation"""
    try:
        return await service.update_calculation(calc_name, request)
    except CalculationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{calc_name}")
async def delete_calculation(
    calc_name: str,
    service: CalculationService = Depends(get_calculation_service)
):
    """Delete a calculation"""
    try:
        return await service.delete_calculation(calc_name)
    except CalculationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/preview-sql")
async def preview_calculation_sql(
    calculation_data: dict,
    service: CalculationService = Depends(get_calculation_service)
):
    """Preview the SQL that would be generated for a calculation"""
    try:
        preview = await service.preview_calculation_sql(calculation_data)
        return preview
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{calc_name}/preview-sql")
async def preview_existing_calculation_sql(
    calc_name: str,
    aggregation_level: Optional[str] = Query("deal", description="Aggregation level: 'deal' or 'tranche'"),
    service: CalculationService = Depends(get_calculation_service)
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
        from app.features.reports.builders.filter_builder import FilterBuilder
        from app.features.reports.builders.query_builder import ReportQueryBuilder
        
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