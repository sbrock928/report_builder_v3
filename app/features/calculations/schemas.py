# app/features/calculations/schemas.py
"""Pydantic schemas for calculations API"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CalculationRequest(BaseModel):
    """Request model for creating/updating calculations"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    formula: str = Field(..., min_length=1)
    aggregation_method: str = Field(...)
    group_level: str = Field(..., description="Aggregation level: 'deal', 'tranche', or 'both'")
    source_tables: List[str] = Field(..., min_items=1)
    dependencies: Optional[List[str]] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "total_ending_balance",
                "description": "Sum of all tranche ending balance amounts",
                "formula": "SUM(tb.tr_end_bal_amt)",
                "aggregation_method": "SUM",
                "source_tables": ["tranchebal tb"],
                "dependencies": []
            }
        }

class CalculationResponse(BaseModel):
    """Response model for calculation definitions"""
    name: str
    description: Optional[str] = None
    formula: str
    aggregation_method: str
    group_level: str
    source_tables: List[str]
    dependencies: List[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "total_ending_balance",
                "description": "Sum of all tranche ending balance amounts",
                "formula": "SUM(tb.tr_end_bal_amt)",
                "aggregation_method": "SUM",
                "source_tables": ["tranchebal tb"],
                "dependencies": [],
                "created_at": "2024-06-03T14:00:00Z",
                "updated_at": "2024-06-03T14:00:00Z"
            }
        }