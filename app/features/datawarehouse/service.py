# app/features/datawarehouse/service.py
"""Business logic for data warehouse operations"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from .repository import DataWarehouseRepository
from .schemas import DealResponse, TrancheResponse, CycleResponse

class DataWarehouseService:
    """Service for data warehouse business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = DataWarehouseRepository(db)
    
    async def get_available_deals(self) -> List[Dict[str, Any]]:
        """Get list of available deals"""
        deals = self.repository.get_all_deals()
        return [{"dl_nbr": deal.dl_nbr} for deal in deals]
    
    async def get_available_tranches(self, deal_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of available tranches, optionally filtered by deal"""
        tranches = self.repository.get_tranches(deal_number)
        return [
            {
                "tr_id": tranche.tr_id,
                "dl_nbr": tranche.dl_nbr,
                "tr_cusip_id": tranche.tr_cusip_id
            }
            for tranche in tranches
        ]
    
    async def get_available_cycles(self) -> List[Dict[str, int]]:
        """Get list of available cycle codes"""
        cycles = self.repository.get_available_cycles()
        return [{"cycle_cde": cycle} for cycle in cycles]