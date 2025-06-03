# app/features/datawarehouse/repository.py
"""Data access layer for data warehouse operations"""

from sqlalchemy.orm import Session
from typing import List, Optional
from .models import Deal, Tranche, TrancheBal

class DataWarehouseDAO:
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
    
    def get_available_cycles(self) -> List[int]:
        """Get distinct cycle codes"""
        result = self.db.query(TrancheBal.cycle_cde).distinct().order_by(TrancheBal.cycle_cde).all()
        return [row[0] for row in result]