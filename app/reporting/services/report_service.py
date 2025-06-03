# app/reporting/services/report_service.py
from typing import List, Dict, Any
import time
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models.request_models import ReportRequest, CalculationRequest
from ..models.response_models import ReportResponse, ReportRow, CalculationResponse
from ..builders.filter_builder import FilterBuilder
from ..builders.report_query_builder import ReportQueryBuilder
from app.datawarehouse.models import Deal, Tranche, TrancheBal
from app.config.models import Calculation, ReportTemplate, ReportExecutionLog

class ReportService:
    """Service for handling report generation and calculation management"""
    
    def __init__(self, dw_db: Session, config_db: Session):
        self.dw_db = dw_db
        self.config_db = config_db
        self.filter_builder = FilterBuilder()
        self.query_builder = ReportQueryBuilder(self.filter_builder)
    
    async def get_available_deals(self) -> List[Dict[str, Any]]:
        """Get list of available deals from data warehouse"""
        deals = self.dw_db.query(Deal).order_by(Deal.dl_nbr).all()
        return [{"dl_nbr": deal.dl_nbr} for deal in deals]
    
    async def get_available_tranches(self, deal_number: int = None) -> List[Dict[str, Any]]:
        """Get list of available tranches, optionally filtered by deal"""
        query = self.dw_db.query(Tranche)
        if deal_number:
            query = query.filter(Tranche.dl_nbr == deal_number)
        
        tranches = query.order_by(Tranche.dl_nbr, Tranche.tr_id).all()
        return [
            {
                "tr_id": tranche.tr_id,
                "dl_nbr": tranche.dl_nbr,
            }
            for tranche in tranches
        ]
    
    async def get_available_cycles(self) -> List[Dict[str, int]]:
        """Get list of available cycle codes"""
        result = self.dw_db.query(TrancheBal.cycle_cde).distinct().order_by(TrancheBal.cycle_cde).all()
        return [{"cycle_cde": row[0]} for row in result]
    
    async def get_available_calculations(self, group_level: str = None) -> List[CalculationResponse]:
        """Get list of available calculations from config database, optionally filtered by group level"""
        query = self.config_db.query(Calculation).filter(Calculation.is_active == True)
        
        if group_level:
            # Show calculations that match the group_level or are marked as 'both'
            query = query.filter(
                (Calculation.group_level == group_level) | (Calculation.group_level == 'both')
            )
        
        calculations = query.order_by(Calculation.name).all()
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
        existing = self.config_db.query(Calculation).filter(
            Calculation.name == request.name
        ).first()
        
        if existing:
            raise ValueError(f"Calculation with name '{request.name}' already exists")
        
        # Create new calculation
        new_calc = Calculation(
            name=request.name,
            description=request.description,
            formula=request.formula,
            aggregation_method=request.aggregation_method,
            group_level=request.group_level,
            source_tables=request.source_tables,
            dependencies=request.dependencies or [],
            created_by=user_id
        )
        
        self.config_db.add(new_calc)
        self.config_db.commit()
        self.config_db.refresh(new_calc)
        
        return CalculationResponse(
            name=new_calc.name,
            description=new_calc.description,
            formula=new_calc.formula,
            aggregation_method=new_calc.aggregation_method,
            group_level=new_calc.group_level,
            source_tables=new_calc.source_tables,
            dependencies=new_calc.dependencies or [],
            created_at=new_calc.created_at,
            updated_at=new_calc.updated_at
        )
    
    async def update_calculation(self, calc_name: str, request: CalculationRequest) -> CalculationResponse:
        """Update an existing calculation"""
        calc = self.config_db.query(Calculation).filter(
            Calculation.name == calc_name
        ).first()
        
        if not calc:
            raise ValueError(f"Calculation '{calc_name}' not found")
        
        # Update fields
        calc.description = request.description
        calc.formula = request.formula
        calc.aggregation_method = request.aggregation_method
        calc.group_level = request.group_level
        calc.source_tables = request.source_tables
        calc.dependencies = request.dependencies or []
        calc.updated_at = datetime.now()
        
        self.config_db.commit()
        self.config_db.refresh(calc)
        
        return CalculationResponse(
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
    
    async def delete_calculation(self, calc_name: str) -> Dict[str, str]:
        """Delete a calculation (soft delete by setting is_active=False)"""
        calc = self.config_db.query(Calculation).filter(
            Calculation.name == calc_name
        ).first()
        
        if not calc:
            raise ValueError(f"Calculation '{calc_name}' not found")
        
        calc.is_active = False
        calc.updated_at = datetime.now()
        
        self.config_db.commit()
        
        return {"message": f"Calculation '{calc_name}' deleted successfully"}
    
    async def generate_report(self, request: ReportRequest) -> ReportResponse:
        """Generate a report with the specified calculations and filters"""
        start_time = time.time()
        
        try:
            # Get calculation configurations from config database
            calc_configs = await self._get_calculation_configs(request.calculations)
            
            # Build and execute the report query
            query, params = self.query_builder.build_report_query(
                calculations=calc_configs,
                aggregation_level=request.aggregation_level.value,
                selected_deals=request.selected_deals,
                selected_tranches=request.selected_tranches,
                cycle_code=request.cycle_code,
                additional_filters=request.filters
            )
            
            # Execute the query
            result = self.dw_db.execute(text(query), params)
            rows = result.fetchall()
            columns = result.keys()

            # Convert to response format
            report_rows = []
            calculation_columns = []
            
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                # Extract dl_nbr, tr_id (if present), and cycle_cde from the row
                dl_nbr = row_dict.get('dl_nbr')
                tr_id = row_dict.get('tr_id')
                cycle_cde = row_dict.get('cycle_cde')
                
                # Create values dict with all calculation results
                values = {}
                for col in columns:
                    if col not in ['dl_nbr', 'tr_id', 'cycle_cde']:  # Skip the ID and cycle columns
                        values[col] = row_dict[col]
                        if col not in calculation_columns:
                            calculation_columns.append(col)
                
                # Create ReportRow with proper structure including cycle_cde
                report_row = ReportRow(
                    dl_nbr=dl_nbr,
                    tr_id=tr_id if request.aggregation_level.value == "tranche" else None,
                    cycle_cde=cycle_cde,  # Add cycle_cde to the response
                    values=values
                )
                report_rows.append(report_row)

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Log the execution
            await self._log_execution(
                report_name=request.report_name,
                aggregation_level=request.aggregation_level.value,
                calculations=request.calculations,
                filters=request.filters,
                execution_time_ms=execution_time_ms,
                row_count=len(report_rows),
                status="success"
            )

            return ReportResponse(
                report_name=request.report_name,
                aggregation_level=request.aggregation_level,
                generated_at=datetime.now(),
                row_count=len(report_rows),
                columns=calculation_columns,  # Only calculation columns
                data=report_rows,
                execution_time_ms=execution_time_ms
            )
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Log the error
            await self._log_execution(
                report_name=request.report_name,
                aggregation_level=request.aggregation_level.value,
                calculations=request.calculations,
                filters=request.filters,
                execution_time_ms=execution_time_ms,
                row_count=0,
                status="error",
                error_message=str(e)
            )
            
            raise e
    
    async def preview_calculation_sql(
        self, 
        calculation_data: Dict[str, Any], 
        sample_filters: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """Generate SQL preview for a calculation"""
        from ..builders.filter_builder import FilterBuilder
        from ..builders.report_query_builder import ReportQueryBuilder
        
        # Create a temporary calculation object
        temp_calculation = {
            'name': calculation_data.get('name', 'preview_calc'),
            'formula': calculation_data.get('formula', ''),
            'aggregation_method': calculation_data.get('aggregation_method', ''),
            'group_level': calculation_data.get('group_level', 'both'),
            'source_tables': calculation_data.get('source_tables', [])
        }
        
        # Create sample filters if none provided
        if not sample_filters:
            sample_filters = {
                'selected_deals': [101, 102, 103],
                'selected_tranches': ['A', 'B'],
                'cycle_code': 202404
            }
        
        # Build SQL for both deal and tranche levels if group_level is 'both'
        filter_builder = FilterBuilder()
        query_builder = ReportQueryBuilder(filter_builder)
        
        result = {}
        
        if temp_calculation['group_level'] in ['deal', 'both']:
            # Generate deal-level SQL
            deal_query, deal_params = query_builder.preview_calculation_subquery(
                temp_calculation, 
                aggregation_level="deal",
                sample_deals=sample_filters['selected_deals'],
                sample_tranches=sample_filters['selected_tranches'],
                sample_cycle=sample_filters['cycle_code']
            )
            result['deal_level_sql'] = deal_query
            result['deal_level_params'] = deal_params
        
        if temp_calculation['group_level'] in ['tranche', 'both']:
            # Generate tranche-level SQL  
            tranche_query, tranche_params = query_builder.preview_calculation_subquery(
                temp_calculation,
                aggregation_level="tranche",
                sample_deals=sample_filters['selected_deals'],
                sample_tranches=sample_filters['selected_tranches'],
                sample_cycle=sample_filters['cycle_code']
            )
            result['tranche_level_sql'] = tranche_query
            result['tranche_level_params'] = tranche_params
        
        return result

    async def preview_report_sql(
        self, 
        report_request: ReportRequest
    ) -> Dict[str, Any]:
        """Generate SQL preview for a complete report"""
        try:
            # Get calculation configurations from config database
            calc_configs = await self._get_calculation_configs(report_request.calculations)
            
            # Build the complete report query
            query, params = self.query_builder.build_report_query(
                calculations=calc_configs,
                aggregation_level=report_request.aggregation_level.value,
                selected_deals=report_request.selected_deals,
                selected_tranches=report_request.selected_tranches,
                cycle_code=report_request.cycle_code,
                additional_filters=report_request.filters
            )
            
            # Also build the simpler aggregation query for comparison
            simple_query, simple_params = self.query_builder.build_simple_aggregation_query(
                calculations=calc_configs,
                aggregation_level=report_request.aggregation_level.value,
                selected_deals=report_request.selected_deals,
                selected_tranches=report_request.selected_tranches,
                cycle_code=report_request.cycle_code,
                additional_filters=report_request.filters
            )
            
            return {
                "report_name": report_request.report_name,
                "aggregation_level": report_request.aggregation_level.value,
                "optimized_query": query,
                "optimized_parameters": params,
                "simple_query": simple_query,
                "simple_parameters": simple_params,
                "selected_calculations": [calc['name'] for calc in calc_configs],
                "filter_summary": {
                    "deals": report_request.selected_deals,
                    "tranches": report_request.selected_tranches,
                    "cycle": report_request.cycle_code,
                    "additional_filters": report_request.filters
                }
            }
            
        except Exception as e:
            raise Exception(f"Failed to generate report SQL preview: {str(e)}")

# app/reporting/services/report_service.py
# Update the _log_execution method:

    async def _log_execution(
        self,
        report_name: str,
        aggregation_level: str,
        calculations: List[str],
        filters: Dict[str, Any],
        execution_time_ms: int,
        row_count: int,
        status: str,
        error_message: str = None
    ):
        """Log report execution to config database"""
        try:
            # Build parameters dict that matches what the user submitted
            parameters = {
                "report_name": report_name,
                "aggregation_level": aggregation_level,
                "calculations": calculations,
                "filters": filters
            }
            
            log_entry = ReportExecutionLog(
                report_name=report_name,
                executed_by="api_user",
                execution_time_ms=float(execution_time_ms),
                row_count=row_count,
                parameters=parameters,  # This matches the JSON field in the model
                success=(status == "success"),
                error_message=error_message
            )
            
            self.config_db.add(log_entry)
            self.config_db.commit()
            
        except Exception as e:
            print(f"Failed to log execution: {e}")
    # Don't raise, as this shouldn't break the main operation
    
    async def _get_calculation_configs(self, calculation_names: List[str]) -> List[Dict[str, Any]]:
        """Get calculation configurations from config database"""
        calculations = self.config_db.query(Calculation).filter(
            Calculation.name.in_(calculation_names),
            Calculation.is_active == True
        ).all()
        
        # Check for missing calculations
        found_names = {calc.name for calc in calculations}
        missing_names = set(calculation_names) - found_names
        
        if missing_names:
            raise ValueError(f"Calculations not found: {', '.join(missing_names)}")
        
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