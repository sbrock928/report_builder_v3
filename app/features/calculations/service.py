# app/features/calculations/service.py
"""Service for refactored calculations management"""

from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.exceptions import CalculationNotFoundError, CalculationAlreadyExistsError, InvalidCalculationError
from .repository import CalculationRepository
from .models import Calculation, AggregationFunction, SourceModel, GroupLevel
from .schemas import CalculationCreateRequest, CalculationResponse

class CalculationService:
    """Service for calculation business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = CalculationRepository(db)
    
    async def get_available_calculations(self, group_level: Optional[str] = None) -> List[CalculationResponse]:
        """Get list of available calculations, optionally filtered by group level"""
        group_level_enum = GroupLevel(group_level) if group_level else None
        calculations = self.repository.get_all_calculations(group_level_enum)
        
        return [
            CalculationResponse.from_orm(calc)
            for calc in calculations
        ]
    
    async def create_calculation(self, request: CalculationCreateRequest, user_id: str = "api_user") -> CalculationResponse:
        """Create a new calculation"""
        # Check if calculation name already exists
        existing = self.repository.get_by_name(request.name)
        if existing:
            raise CalculationAlreadyExistsError(f"Calculation with name '{request.name}' already exists")
        
        # Validate weighted average has weight field
        if request.aggregation_function == AggregationFunction.WEIGHTED_AVG and not request.weight_field:
            raise InvalidCalculationError("Weighted average calculations require a weight_field")
        
        # Create new calculation
        calculation = Calculation(
            name=request.name,
            description=request.description,
            aggregation_function=request.aggregation_function,
            source_model=request.source_model,
            source_field=request.source_field,
            group_level=request.group_level,
            weight_field=request.weight_field,
            created_by=user_id
        )
        
        calculation = self.repository.create(calculation)
        return CalculationResponse.from_orm(calculation)
    
    async def update_calculation(self, calc_id: int, request: CalculationCreateRequest) -> CalculationResponse:
        """Update an existing calculation"""
        calculation = self.repository.get_by_id(calc_id)
        if not calculation:
            raise CalculationNotFoundError(f"Calculation with ID {calc_id} not found")
        
        # Validate weighted average has weight field
        if request.aggregation_function == AggregationFunction.WEIGHTED_AVG and not request.weight_field:
            raise InvalidCalculationError("Weighted average calculations require a weight_field")
        
        # Update fields
        calculation.description = request.description
        calculation.aggregation_function = request.aggregation_function
        calculation.source_model = request.source_model
        calculation.source_field = request.source_field
        calculation.group_level = request.group_level
        calculation.weight_field = request.weight_field
        
        calculation = self.repository.update(calculation)
        return CalculationResponse.from_orm(calculation)
    
    async def delete_calculation(self, calc_id: int) -> dict:
        """Delete a calculation (soft delete)"""
        calculation = self.repository.get_by_id(calc_id)
        if not calculation:
            raise CalculationNotFoundError(f"Calculation with ID {calc_id} not found")
        
        self.repository.soft_delete(calculation)
        return {"message": f"Calculation '{calculation.name}' deleted successfully"}