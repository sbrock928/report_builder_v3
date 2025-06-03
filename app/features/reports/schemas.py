# app/features/reports/schemas.py
"""Pydantic schemas for reports API"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
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

class ReportRow(BaseModel):
    """Single row in a report result"""
    dl_nbr: int
    tr_id: Optional[str] = None  # Only present for tranche-level reports
    cycle_cde: Optional[int] = None  # Cycle code for the data
    values: Dict[str, Any]  # Calculation results keyed by calculation name

    class Config:
        json_schema_extra = {
            "example": {
                "dl_nbr": 101,
                "tr_id": "A",
                "cycle_cde": 202403,
                "values": {
                    "total_ending_balance": 50000000.00,
                    "total_principal_released": 1500000.00
                }
            }
        }

class ReportResponse(BaseModel):
    """Response model for generated reports"""
    report_name: str
    aggregation_level: AggregationLevel
    generated_at: datetime
    row_count: int
    columns: List[str]  # List of calculation names
    data: List[ReportRow]
    execution_time_ms: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "report_name": "Q4 Deal Analysis",
                "aggregation_level": "deal",
                "generated_at": "2024-06-03T14:30:00Z",
                "row_count": 2,
                "columns": ["total_ending_balance", "total_principal_released"],
                "data": [
                    {
                        "dl_nbr": 101,
                        "tr_id": None,
                        "cycle_cde": 202403,
                        "values": {
                            "total_ending_balance": 50000000.00,
                            "total_principal_released": 1500000.00
                        }
                    }
                ],
                "execution_time_ms": 250.5
            }
        }