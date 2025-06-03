# app/features/datawarehouse/router.py
"""API endpoints for data warehouse operations"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
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
    deal_number: Optional[int] = Query(None, description="Filter tranches by deal number"),
    service: DataWarehouseService = Depends(get_datawarehouse_service)
):
    """Get list of available tranches, optionally filtered by deal"""
    return await service.get_available_tranches(deal_number)

@router.get("/cycles")
async def get_available_cycles(
    service: DataWarehouseService = Depends(get_datawarehouse_service)
):
    """Get list of available cycle codes"""
    return await service.get_available_cycles()