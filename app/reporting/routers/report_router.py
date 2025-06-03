# app/reporting/routers/report_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..models.request_models import ReportRequest, CalculationRequest, AggregationLevel
from ..models.response_models import ReportResponse, CalculationResponse
from ..services.report_service import ReportService
from app.core.database import get_dw_session, get_config_session

router = APIRouter(prefix="/api/reports", tags=["reports"])

def get_report_service(
    dw_db: Session = Depends(get_dw_session),
    config_db: Session = Depends(get_config_session)
) -> ReportService:
    return ReportService(dw_db, config_db)

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    service: ReportService = Depends(get_report_service)
):
    """Generate a report with specified calculations and filters"""
    try:
        # In a real app, you'd get user_id from authentication
        user_id = "current_user"  # Replace with actual user authentication
        return await service.generate_report(request, user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/calculations", response_model=List[CalculationResponse])
async def get_available_calculations(
    service: ReportService = Depends(get_report_service)
):
    """Get list of available calculations"""
    return await service.get_available_calculations()

@router.post("/calculations", response_model=CalculationResponse)
async def create_calculation(
    request: CalculationRequest,
    service: ReportService = Depends(get_report_service)
):
    """Create a new custom calculation"""
    try:
        user_id = "current_user"  # Replace with actual user authentication
        return await service.create_calculation(request, user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/calculations/{calc_name}", response_model=CalculationResponse)
async def update_calculation(
    calc_name: str,
    request: CalculationRequest,
    service: ReportService = Depends(get_report_service)
):
    """Update an existing calculation"""
    try:
        user_id = "current_user"  # Replace with actual user authentication
        return await service.update_calculation(calc_name, request, user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/calculations/{calc_name}")
async def delete_calculation(
    calc_name: str,
    service: ReportService = Depends(get_report_service)
):
    """Delete (deactivate) a calculation"""
    try:
        success = await service.delete_calculation(calc_name)
        return {"success": success, "message": f"Calculation '{calc_name}' deactivated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/deals")
async def get_available_deals(service: ReportService = Depends(get_report_service)):
    """Get list of available deals for filtering"""
    return await service.get_available_deals()

@router.get("/tranches")
async def get_available_tranches(
    deal_numbers: Optional[str] = Query(None, description="Comma-separated deal numbers"),
    service: ReportService = Depends(get_report_service)
):
    """Get list of available tranches, optionally filtered by deals"""
    deal_list = None
    if deal_numbers:
        try:
            deal_list = [int(x.strip()) for x in deal_numbers.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid deal numbers format")
    
    return await service.get_available_tranches(deal_list)

@router.get("/cycles")
async def get_available_cycles(service: ReportService = Depends(get_report_service)):
    """Get list of available cycle codes"""
    return await service.get_available_cycles()
