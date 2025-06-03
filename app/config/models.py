# app/config/models.py
"""
DEPRECATED: Legacy models file - now redirects to new feature-based models
All models have been migrated to the features modules for better organization.
"""

# Import new models for backward compatibility
from app.features.calculations.models import (
    Calculation,
    AggregationFunction,
    SourceModel,
    GroupLevel
)

from app.features.reports.models import (
    Report,
    ReportDeal,
    ReportTranche,
    ReportCalculation,
    ReportExecutionLog
)

# Backward compatibility aliases
ReportTemplate = Report  # Old name for Report model

__all__ = [
    "Calculation",
    "AggregationFunction", 
    "SourceModel",
    "GroupLevel",
    "Report",
    "ReportTemplate",  # Alias for compatibility
    "ReportDeal",
    "ReportTranche", 
    "ReportCalculation",
    "ReportExecutionLog"
]

