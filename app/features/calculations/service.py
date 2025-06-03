# app/features/calculations/service.py
"""Business logic for calculations management"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.exceptions import CalculationNotFoundError, CalculationAlreadyExistsError
from .repository import CalculationRepository
from .schemas import CalculationRequest, CalculationResponse

class CalculationService:
    """Service for calculation business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = CalculationRepository(db)
    
    async def get_available_calculations(self, group_level: Optional[str] = None) -> List[CalculationResponse]:
        """Get list of available calculations, optionally filtered by group level"""
        calculations = self.repository.get_all_calculations(group_level)
        
        return [
            CalculationResponse(
                name=calc.name,
                description=calc.description,
                formula=calc.formula,
                aggregation_method=calc.aggregation_method,
                group_level=calc.group_level,
                source_tables=calc.source_tables,
                dependencies=calc.dependencies or [],
                created_at=calc.created_at,
                updated_at=calc.updated_at
            )
            for calc in calculations
        ]
    
    async def create_calculation(self, request: CalculationRequest, user_id: str = "api_user") -> CalculationResponse:
        """Create a new calculation"""
        # Check if calculation name already exists
        existing = self.repository.get_by_name(request.name)
        if existing:
            raise CalculationAlreadyExistsError(f"Calculation with name '{request.name}' already exists")
        
        # Create new calculation
        calculation_data = {
            "name": request.name,
            "description": request.description,
            "formula": request.formula,
            "aggregation_method": request.aggregation_method,
            "group_level": request.group_level,
            "source_tables": request.source_tables,
            "dependencies": request.dependencies or [],
            "created_by": user_id
        }
        
        calculation = self.repository.create(calculation_data)
        
        return CalculationResponse(
            name=calculation.name,
            description=calculation.description,
            formula=calculation.formula,
            aggregation_method=calculation.aggregation_method,
            group_level=calculation.group_level,
            source_tables=calculation.source_tables,
            dependencies=calculation.dependencies or [],
            created_at=calculation.created_at,
            updated_at=calculation.updated_at
        )
    
    async def update_calculation(self, calc_name: str, request: CalculationRequest) -> CalculationResponse:
        """Update an existing calculation"""
        calculation = self.repository.get_by_name(calc_name)
        if not calculation:
            raise CalculationNotFoundError(f"Calculation '{calc_name}' not found")
        
        # Update fields
        update_data = {
            "description": request.description,
            "formula": request.formula,
            "aggregation_method": request.aggregation_method,
            "group_level": request.group_level,
            "source_tables": request.source_tables,
            "dependencies": request.dependencies or []
        }
        
        calculation = self.repository.update(calculation, update_data)
        
        return CalculationResponse(
            name=calculation.name,
            description=calculation.description,
            formula=calculation.formula,
            aggregation_method=calculation.aggregation_method,
            group_level=calculation.group_level,
            source_tables=calculation.source_tables,
            dependencies=calculation.dependencies or [],
            created_at=calculation.created_at,
            updated_at=calculation.updated_at
        )
    
    async def delete_calculation(self, calc_name: str) -> Dict[str, str]:
        """Delete a calculation (soft delete by setting is_active=False)"""
        calculation = self.repository.get_by_name(calc_name)
        if not calculation:
            raise CalculationNotFoundError(f"Calculation '{calc_name}' not found")
        
        self.repository.soft_delete(calculation)
        
        return {"message": f"Calculation '{calc_name}' deleted successfully"}
    
    async def get_calculation_configs(self, calculation_names: List[str]) -> List[Dict[str, Any]]:
        """Get calculation configurations for report generation"""
        calculations = self.repository.get_by_names(calculation_names)
        
        # Check for missing calculations
        found_names = {calc.name for calc in calculations}
        missing_names = set(calculation_names) - found_names
        
        if missing_names:
            raise CalculationNotFoundError(f"Calculations not found: {', '.join(missing_names)}")
        
        return [
            {
                'name': calc.name,
                'formula': calc.formula,
                'source_tables': calc.source_tables,
                'aggregation_method': calc.aggregation_method,
                'group_level': calc.group_level
            }
            for calc in calculations
        ]
    
    async def preview_calculation_sql(
        self, 
        calculation_data: Dict[str, Any], 
        sample_filters: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """Generate SQL preview for a calculation"""
        from app.features.reports.builders.filter_builder import FilterBuilder
        from app.features.reports.builders.query_builder import ReportQueryBuilder
        
        # Create a temporary calculation object
        temp_calculation = {
            'name': calculation_data.get('name', 'preview_calc'),
            'formula': calculation_data.get('formula', ''),
            'aggregation_method': calculation_data.get('aggregation_method', ''),
            'group_level': calculation_data.get('group_level', 'deal'),
            'source_tables': calculation_data.get('source_tables', [])
        }
        
        # Create sample filters if none provided
        if not sample_filters:
            sample_filters = {
                'selected_deals': [101, 102, 103],
                'selected_tranches': ['A', 'B'],
                'cycle_code': 202404
            }
        
        # Build SQL for the specific group level only
        filter_builder = FilterBuilder()
        query_builder = ReportQueryBuilder(filter_builder)
        
        result = {}
        group_level = temp_calculation['group_level']
        
        # Generate SQL for the specific level
        query, params = query_builder.preview_calculation_subquery(
            temp_calculation, 
            aggregation_level=group_level,
            sample_deals=sample_filters['selected_deals'],
            sample_tranches=sample_filters['selected_tranches'],
            sample_cycle=sample_filters['cycle_code']
        )
        
        if group_level == 'deal':
            result['deal_level_sql'] = query
            result['deal_level_params'] = params
        else:
            result['tranche_level_sql'] = query
            result['tranche_level_params'] = params
        
        return result