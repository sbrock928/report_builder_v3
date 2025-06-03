# app/features/datawarehouse/router.py
"""API endpoints for data warehouse operations"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.dependencies import get_dw_db
from .service import DataWarehouseService

router = APIRouter()

def get_datawarehouse_service(db: Session = Depends(get_dw_db)) -> DataWarehouseService:
    """Get data warehouse service with database session"""
    return DataWarehouseService(db)

@router.get("/deals")
async def get_available_deals(
    service: DataWarehouseService = Depends(get_datawarehouse_service)
):
    """Get list of available deals"""
    return await service.get_available_deals()

@router.get("/tranches")
async def get_available_tranches(
    service: DataWarehouseService = Depends(get_datawarehouse_service),
    deal_number: Optional[int] = Query(None, description="Filter tranches by deal number"),
    deal_numbers: Optional[str] = Query(None, description="Comma-separated deal numbers")
):
    """Get list of available tranches, optionally filtered by deal(s)"""
    # Handle both single deal_number and comma-separated deal_numbers
    if deal_numbers:
        try:
            deal_list = [int(x.strip()) for x in deal_numbers.split(',') if x.strip()]
            return await service.get_available_tranches(deal_list=deal_list)
        except ValueError:
            return {"error": "Invalid deal_numbers format"}
    elif deal_number:
        return await service.get_available_tranches(deal_number=deal_number)
    else:
        return await service.get_available_tranches()

@router.get("/cycles")
async def get_available_cycles(
    service: DataWarehouseService = Depends(get_datawarehouse_service)
):
    """Get list of available cycle codes"""
    return await service.get_available_cycles()