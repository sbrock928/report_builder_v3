# app/shared/utils.py
"""Shared utility functions"""

import re
from typing import Dict, Any, List

def sanitize_identifier(name: str) -> str:
    """Sanitize a string for use as SQL identifier"""
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = f"calc_{sanitized}"
    return sanitized or "calculation"

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate that required fields are present and not empty"""
    errors = []
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"{field} is required")
    return errors

def format_execution_time(time_ms: float) -> str:
    """Format execution time in a human-readable format"""
    if time_ms < 1000:
        return f"{time_ms:.1f}ms"
    elif time_ms < 60000:
        return f"{time_ms/1000:.1f}s"
    else:
        minutes = int(time_ms / 60000)
        seconds = (time_ms % 60000) / 1000
        return f"{minutes}m {seconds:.1f}s"