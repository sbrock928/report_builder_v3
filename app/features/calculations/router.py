# app/features/calculations/router.py
"""Refactored calculations router using unified query engine"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.dependencies import get_config_only_db, get_query_engine
from app.core.exceptions import CalculationNotFoundError, CalculationAlreadyExistsError, InvalidCalculationError
from app.shared.query_engine import QueryEngine
from .service import CalculationService
from .schemas import CalculationCreateRequest, CalculationResponse

router = APIRouter()

def get_calculation_service(config_db: Session = Depends(get_config_only_db)) -> CalculationService:
    """Get calculation service for config-only operations"""
    return CalculationService(config_db)

def get_calculation_service_with_preview(query_engine: QueryEngine = Depends(get_query_engine)) -> CalculationService:
    """Get calculation service with query engine for preview operations"""
    return CalculationService(query_engine.config_db, query_engine)

@router.get("", response_model=List[CalculationResponse])
async def get_available_calculations(
    service: CalculationService = Depends(get_calculation_service),
    group_level: Optional[str] = Query(None, description="Filter by group level: 'deal', 'tranche'")
):
    """Get list of available calculations, optionally filtered by group level"""
    return await service.get_available_calculations(group_level)

@router.post("", response_model=CalculationResponse, status_code=201)
async def create_calculation(
    request: CalculationCreateRequest,
    service: CalculationService = Depends(get_calculation_service)
):
    """Create a new calculation"""
    try:
        return await service.create_calculation(request)
    except (CalculationAlreadyExistsError, InvalidCalculationError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{calc_id}/preview-sql")
async def preview_calculation_sql(
    calc_id: int,
    service: CalculationService = Depends(get_calculation_service_with_preview),
    aggregation_level: str = Query("deal", description="Aggregation level: 'deal' or 'tranche'"),
    sample_deals: str = Query("101,102,103", description="Comma-separated sample deal numbers"),
    sample_tranches: str = Query("A,B", description="Comma-separated sample tranche IDs"),
    sample_cycle: int = Query(202404, description="Sample cycle code")
):
    """Preview SQL using unified query engine"""
    try:
        # Parse comma-separated values
        deal_list = [int(d.strip()) for d in sample_deals.split(',') if d.strip()]
        tranche_list = [t.strip() for t in sample_tranches.split(',') if t.strip()]
        
        return await service.preview_calculation_sql(
            calc_id, aggregation_level, deal_list, tranche_list, sample_cycle
        )
    except CalculationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{calc_id}", response_model=CalculationResponse)
async def update_calculation(
    calc_id: int,
    request: CalculationCreateRequest,
    service: CalculationService = Depends(get_calculation_service)
):
    """Update an existing calculation"""
    try:
        return await service.update_calculation(calc_id, request)
    except CalculationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidCalculationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{calc_id}")
async def delete_calculation(
    calc_id: int,
    service: CalculationService = Depends(get_calculation_service)
):
    """Delete a calculation"""
    try:
        return await service.delete_calculation(calc_id)
    except CalculationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))