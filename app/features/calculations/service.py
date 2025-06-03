# app/features/calculations/service.py
"""Service for refactored calculations management"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Tuple
from app.core.exceptions import CalculationNotFoundError, CalculationAlreadyExistsError, InvalidCalculationError
from app.shared.sql_preview_service import SqlPreviewService
from .repository import CalculationRepository
from .models import Calculation, AggregationFunction, SourceModel, GroupLevel
from .schemas import CalculationCreateRequest, CalculationResponse

class CalculationService:
    """Service for calculation business logic"""
    
    def __init__(self, db: Session, dw_db: Session = None):
        self.db = db
        self.dw_db = dw_db
        self.repository = CalculationRepository(db)
        # Initialize shared SQL preview service if data warehouse DB is provided
        if dw_db:
            self.sql_preview_service = SqlPreviewService(dw_db, db)
    
    async def get_available_calculations(self, group_level: Optional[str] = None) -> List[CalculationResponse]:
        """Get list of available calculations, optionally filtered by group level"""
        group_level_enum = GroupLevel(group_level) if group_level else None
        calculations = self.repository.get_all_calculations(group_level_enum)
        
        return [
            CalculationResponse.from_orm(calc)
            for calc in calculations
        ]
    
    async def preview_calculation_sql(
        self,
        calc_id: int,
        aggregation_level: str = "deal",
        sample_deals: List[int] = None,
        sample_tranches: List[str] = None,
        sample_cycle: int = None
    ) -> Dict[str, Any]:
        """Generate SQL preview for an existing calculation using shared ORM logic"""
        calculation = self.db.query(Calculation).filter(
            Calculation.id == calc_id,
            Calculation.is_active == True
        ).first()
        
        if not calculation:
            raise CalculationNotFoundError(f"Calculation with ID {calc_id} not found")
        
        if not self.sql_preview_service:
            raise ValueError("Data warehouse database session required for SQL preview")
        
        # Use the shared preview service that uses the same ORM logic as report execution
        return self.sql_preview_service.preview_calculation_sql(
            calculation=calculation,
            aggregation_level=aggregation_level,
            sample_deals=sample_deals,
            sample_tranches=sample_tranches,
            sample_cycle=sample_cycle
        )

    def _build_formula_from_calculation(self, calculation: Calculation) -> str:
        """Build SQL formula from ORM calculation definition"""
        # Map source model to table alias
        model_to_table = {
            "Deal": "d",
            "Tranche": "t", 
            "TrancheBal": "tb"
        }
        
        table_alias = model_to_table.get(calculation.source_model.value, "d")
        field_ref = f"{table_alias}.{calculation.source_field}"
        
        if calculation.aggregation_function == AggregationFunction.WEIGHTED_AVG:
            if not calculation.weight_field:
                raise ValueError(f"Weighted average calculation requires weight_field")
            weight_ref = f"{table_alias}.{calculation.weight_field}"
            return f"SUM({field_ref} * {weight_ref}) / NULLIF(SUM({weight_ref}), 0)"
        else:
            func_name = calculation.aggregation_function.value
            return f"{func_name}({field_ref})"

    def _get_source_tables_from_calculation(self, calculation: Calculation) -> List[str]:
        """Get required source tables for this calculation"""
        tables = []
        
        if calculation.source_model in [SourceModel.TRANCHE, SourceModel.TRANCHE_BAL]:
            tables.append("tranche t")
        
        if calculation.source_model == SourceModel.TRANCHE_BAL:
            tables.append("tranchebal tb")
        
        return tables

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