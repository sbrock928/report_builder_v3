# app/shared/constants.py
"""Shared constants for the application"""

from enum import Enum

class AggregationLevel(str, Enum):
    """Aggregation levels for reports and calculations"""
    DEAL = "deal"
    TRANCHE = "tranche"

class AggregationMethod(str, Enum):
    """Available aggregation methods for calculations"""
    SUM = "SUM"
    AVG = "AVG"
    COUNT = "COUNT"
    MIN = "MIN"
    MAX = "MAX"
    WEIGHTED_AVG = "WEIGHTED_AVG"

class SourceTable(str, Enum):
    """Available source tables in the data warehouse"""
    DEAL = "deal d"
    TRANCHE = "tranche t"
    TRANCHE_BAL = "tranchebal tb"

# Default user for API operations
DEFAULT_API_USER = "api_user"

# Database connection settings
DEFAULT_DW_DATABASE_PATH = "./data_warehouse.db"
DEFAULT_CONFIG_DATABASE_PATH = "./config.db"

# Execution logging settings
MAX_ERROR_MESSAGE_LENGTH = 1000
DEFAULT_EXECUTION_TIMEOUT_MS = 30000  # 30 seconds