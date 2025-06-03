# app/features/calculations/repository.py
"""Data access layer for calculations"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from .models import Calculation

class CalculationRepository:
    """Repository for calculation data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_calculations(self, group_level: Optional[str] = None) -> List[Calculation]:
        """Get all active calculations, optionally filtered by group level"""
        query = self.db.query(Calculation).filter(Calculation.is_active == True)
        
        if group_level:
            query = query.filter(Calculation.group_level == group_level)
        
        return query.order_by(Calculation.name).all()
    
    def get_by_name(self, name: str) -> Optional[Calculation]:
        """Get calculation by name"""
        return self.db.query(Calculation).filter(
            Calculation.name == name,
            Calculation.is_active == True
        ).first()
    
    def get_by_names(self, names: List[str]) -> List[Calculation]:
        """Get calculations by list of names"""
        return self.db.query(Calculation).filter(
            Calculation.name.in_(names),
            Calculation.is_active == True
        ).all()
    
    def create(self, calculation_data: dict) -> Calculation:
        """Create a new calculation"""
        calculation = Calculation(**calculation_data)
        self.db.add(calculation)
        self.db.commit()
        self.db.refresh(calculation)
        return calculation
    
    def update(self, calculation: Calculation, update_data: dict) -> Calculation:
        """Update an existing calculation"""
        for key, value in update_data.items():
            setattr(calculation, key, value)
        
        calculation.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(calculation)
        return calculation
    
    def soft_delete(self, calculation: Calculation) -> Calculation:
        """Soft delete a calculation by setting is_active=False"""
        calculation.is_active = False
        calculation.updated_at = datetime.now()
        self.db.commit()
        return calculation