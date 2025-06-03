# app/reporting/models/response_models.py
"""Pydantic models for API responses"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .request_models import AggregationLevel

class ReportRow(BaseModel):
    """Single row in a report result"""
    dl_nbr: int
    tr_id: Optional[str] = None  # Only present for tranche-level reports
    values: Dict[str, Any]  # Calculation results keyed by calculation name

    class Config:
        json_schema_extra = {
            "example": {
                "dl_nbr": 101,
                "tr_id": "A",
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
                        "values": {
                            "total_ending_balance": 50000000.00,
                            "total_principal_released": 1500000.00
                        }
                    }
                ],
                "execution_time_ms": 250.5
            }
        }

class CalculationResponse(BaseModel):
    """Response model for calculation definitions"""
    name: str
    description: Optional[str] = None
    formula: str
    aggregation_method: str
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