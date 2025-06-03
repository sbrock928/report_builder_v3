# app/features/datawarehouse/service.py
"""Fixed datawarehouse service without circular imports"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from .models import Deal, Tranche, TrancheBal

class DataWarehouseService:
    """Simplified data warehouse service using direct database access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_available_deals(self) -> List[Dict[str, Any]]:
        """Get list of available deals"""
        deals = self.db.query(Deal).order_by(Deal.dl_nbr).all()
        
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
        
        query = self.db.query(Tranche)
        
        if deal_list:
            query = query.filter(Tranche.dl_nbr.in_(deal_list))
        elif deal_number:
            query = query.filter(Tranche.dl_nbr == deal_number)
            
        tranches = query.order_by(Tranche.dl_nbr, Tranche.tr_id).all()
            
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
        result = self.db.query(TrancheBal.cycle_cde)\
            .distinct().order_by(TrancheBal.cycle_cde).all()
        cycles = [row[0] for row in result]
        return [{"cycle_cde": cycle} for cycle in cycles]