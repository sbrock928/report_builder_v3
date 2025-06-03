# app/reporting/models/request_models.py
"""Pydantic models for API requests"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class AggregationLevel(str, Enum):
    deal = "deal"
    tranche = "tranche"

class ReportRequest(BaseModel):
    """Request model for generating reports"""
    report_name: str = Field(..., min_length=1, max_length=200)
    aggregation_level: AggregationLevel
    selected_deals: List[int] = Field(..., min_items=1)
    selected_tranches: List[str] = Field(..., min_items=1)
    cycle_code: int = Field(..., gt=0)
    calculations: List[str] = Field(..., min_items=1)
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "report_name": "Q4 Deal Analysis",
                "aggregation_level": "deal",
                "selected_deals": [101, 102],
                "selected_tranches": ["A", "B"],
                "cycle_code": 202404,
                "calculations": ["total_ending_balance", "total_principal_released"],
                "filters": {}
            }
        }

class CalculationRequest(BaseModel):
    """Request model for creating/updating calculations"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    formula: str = Field(..., min_length=1)
    aggregation_method: str = Field(...)
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