# app/features/reports/schemas.py
"""Updated schemas without cycle_code in template creation"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AggregationLevel(str, Enum):
    deal = "deal"
    tranche = "tranche"

# Request schemas for creating/updating reports
class ReportCreateRequest(BaseModel):
    """Request model for creating a new report template (no cycle_code)"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    aggregation_level: AggregationLevel
    selected_deals: List[int] = Field(..., min_items=1)
    selected_tranches: List[str] = Field(..., min_items=1)
    selected_calculations: List[str] = Field(..., min_items=1)  # Calculation names

class ReportUpdateRequest(BaseModel):
    """Request model for updating an existing report template (no cycle_code)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    selected_deals: Optional[List[int]] = Field(None, min_items=1)
    selected_tranches: Optional[List[str]] = Field(None, min_items=1)
    selected_calculations: Optional[List[str]] = Field(None, min_items=1)

class ReportExecuteRequest(BaseModel):
    """Request model for executing a report (cycle_code is required)"""
    cycle_code: int = Field(..., gt=0, description="Cycle code to run the report for")

# Response schemas
class ReportRow(BaseModel):
    """Single row in a report result"""
    dl_nbr: int
    tr_id: Optional[str] = None  # Only present for tranche-level reports
    cycle_cde: int
    values: Dict[str, Any]  # Calculation results keyed by calculation name

class ReportResponse(BaseModel):
    """Response model for generated reports"""
    report_id: int
    report_name: str
    aggregation_level: str
    cycle_code: int  # Shows the cycle that was executed
    generated_at: datetime
    row_count: int
    columns: List[str]  # List of calculation names
    data: List[ReportRow]
    execution_time_ms: Optional[float] = None

class ReportTemplateResponse(BaseModel):
    """Response model for report template metadata (no cycle_code)"""
    id: int
    name: str
    description: Optional[str]
    aggregation_level: str
    deal_count: int
    tranche_count: int
    calculation_count: int
    last_executed_cycle: Optional[int] = None  # Most recent cycle executed
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

class ReportTemplateDetailResponse(BaseModel):
    """Detailed response model for report template (no cycle_code)"""
    id: int
    name: str
    description: Optional[str]
    aggregation_level: str
    selected_deals: List[int]
    selected_tranches: List[str]
    selected_calculations: List[str]
    recent_executions: Optional[List[Dict[str, Any]]] = None  # Recent execution history
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]