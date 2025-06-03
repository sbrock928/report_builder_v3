# app/features/datawarehouse/schemas.py
"""Pydantic schemas for data warehouse API responses"""

from pydantic import BaseModel
from typing import List, Optional

class DealResponse(BaseModel):
    """Response model for Deal data"""
    dl_nbr: int
    issr_cde: Optional[str] = None
    cdi_file_nme: Optional[str] = None
    
    class Config:
        from_attributes = True

class TrancheResponse(BaseModel):
    """Response model for Tranche data"""
    dl_nbr: int
    tr_id: str
    tr_cusip_id: str
    
    class Config:
        from_attributes = True

class CycleResponse(BaseModel):
    """Response model for available cycle codes"""
    cycle_cde: int