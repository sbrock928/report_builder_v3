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
        return [
            {
                "dl_nbr": deal.dl_nbr,
                "issr_cde": deal.issr_cde,
                "cdi_file_nme": deal.cdi_file_nme
            } 
            for deal in deals
        ]
    
    async def get_available_tranches(
        self, 
        deal_number: Optional[int] = None,
        deal_list: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Get list of available tranches, optionally filtered by deal(s)"""
        
        if deal_list:
            # Filter by multiple deals
            tranches = self.repository.get_tranches_by_deals(deal_list)
        elif deal_number:
            # Filter by single deal
            tranches = self.repository.get_tranches(deal_number)
        else:
            # Get all tranches
            tranches = self.repository.get_tranches()
            
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


# app/features/datawarehouse/repository.py
"""Data access layer for data warehouse operations"""

from sqlalchemy.orm import Session
from typing import List, Optional
from .models import Deal, Tranche, TrancheBal

class DataWarehouseRepository:
    """Repository for data warehouse data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_deals(self) -> List[Deal]:
        """Get all deals from data warehouse"""
        return self.db.query(Deal).order_by(Deal.dl_nbr).all()
    
    def get_tranches(self, deal_number: Optional[int] = None) -> List[Tranche]:
        """Get tranches, optionally filtered by deal"""
        query = self.db.query(Tranche)
        if deal_number:
            query = query.filter(Tranche.dl_nbr == deal_number)
        return query.order_by(Tranche.dl_nbr, Tranche.tr_id).all()
    
    def get_tranches_by_deals(self, deal_numbers: List[int]) -> List[Tranche]:
        """Get tranches filtered by multiple deals"""
        return self.db.query(Tranche)\
            .filter(Tranche.dl_nbr.in_(deal_numbers))\
            .order_by(Tranche.dl_nbr, Tranche.tr_id).all()
    
    def get_available_cycles(self) -> List[int]:
        """Get distinct cycle codes"""
        result = self.db.query(TrancheBal.cycle_cde).distinct().order_by(TrancheBal.cycle_cde).all()
        return [row[0] for row in result]