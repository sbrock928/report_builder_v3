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
    """Business logic for report generation using dual database approach"""
    
    def __init__(self, dw_session: Session, config_session: Session):
        self.dw_db = dw_session  # Data warehouse for queries
        self.config_db = config_session  # Config DB for calculations/templates
        self.filter_builder = FilterBuilder()
        self.query_builder = ReportQueryBuilder(self.filter_builder, None)
    
    async def generate_report(self, request: ReportRequest, user_id: str = None) -> ReportResponse:
        """Generate a report based on the request parameters"""
        start_time = time.time()
        success = True
        error_message = None
        
        try:
            # Get calculation configurations from config database
            calc_configs = await self._get_calculation_configs(request.calculations)
            
            # Build and execute query on data warehouse
            query, params = self.query_builder.build_report_query(
                calculations=calc_configs,
                aggregation_level=request.aggregation_level.value,
                selected_deals=request.selected_deals,
                selected_tranches=request.selected_tranches,
                cycle_code=request.cycle_code,
                additional_filters=request.filters
            )
            
            # Execute query on data warehouse
            result = self.dw_db.execute(text(query), params)
            rows = result.fetchall()
            columns = list(result.keys())
            
            # Format response
            report_rows = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                # Extract deal number and tranche ID
                dl_nbr = row_dict.pop('dl_nbr')
                tr_id = row_dict.pop('tr_id', None) if request.aggregation_level == "tranche" else None
                
                # Remaining columns are calculation values
                values = {k: v for k, v in row_dict.items() if k.startswith('calc_')}
                # Clean up calculation names (remove 'calc_' prefix)
                values = {k.replace('calc_', ''): v for k, v in values.items()}
                
                report_rows.append(ReportRow(
                    dl_nbr=dl_nbr,
                    tr_id=tr_id,
                    values=values
                ))
            
            execution_time = (time.time() - start_time) * 1000
            
            response = ReportResponse(
                report_name=request.report_name,
                aggregation_level=request.aggregation_level,
                generated_at=datetime.now(),
                row_count=len(report_rows),
                columns=request.calculations,
                data=report_rows,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            success = False
            error_message = str(e)
            execution_time = (time.time() - start_time) * 1000
            raise
        
        finally:
            # Log execution to config database
            await self._log_execution(
                report_name=request.report_name,
                user_id=user_id,
                execution_time=execution_time,
                row_count=len(report_rows) if success else None,
                parameters=request.dict(),
                success=success,
                error_message=error_message
            )
        
        return response
    
    async def _get_calculation_configs(self, calculation_names: List[str]) -> List[Dict[str, Any]]:
        """Get calculation configurations from config database"""
        calculations = self.config_db.query(Calculation).filter(
            Calculation.name.in_(calculation_names),
            Calculation.is_active == True
        ).all()
        
        if len(calculations) != len(calculation_names):
            found_names = [calc.name for calc in calculations]
            missing = [name for name in calculation_names if name not in found_names]
            raise ValueError(f"Unknown calculations: {missing}")
        
        return [
            {
                "name": calc.name,
                "description": calc.description,
                "formula": calc.formula,
                "aggregation_method": calc.aggregation_method,
                "source_tables": calc.source_tables,
                "dependencies": calc.dependencies or []
            }
            for calc in calculations
        ]
    
    async def get_available_calculations(self) -> List[CalculationResponse]:
        """Get list of available calculations from config database"""
        calculations = self.config_db.query(Calculation).filter(
            Calculation.is_active == True
        ).order_by(Calculation.name).all()
        
        return [
            CalculationResponse(
                name=calc.name,
                description=calc.description,
                formula=calc.formula,
                aggregation_method=calc.aggregation_method,
                source_tables=calc.source_tables,
                dependencies=calc.dependencies or [],
                created_at=calc.created_at,
                updated_at=calc.updated_at
            )
            for calc in calculations
        ]
    
    async def create_calculation(self, request: CalculationRequest, user_id: str = None) -> CalculationResponse:
        """Create a new custom calculation in config database"""
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
            source_tables=new_calc.source_tables,
            dependencies=new_calc.dependencies or [],
            created_at=new_calc.created_at,
            updated_at=new_calc.updated_at
        )
    
    async def update_calculation(self, calc_name: str, request: CalculationRequest, user_id: str = None) -> CalculationResponse:
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
            source_tables=calc.source_tables,
            dependencies=calc.dependencies or [],
            created_at=calc.created_at,
            updated_at=calc.updated_at
        )
    
    async def delete_calculation(self, calc_name: str) -> bool:
        """Soft delete a calculation"""
        calc = self.config_db.query(Calculation).filter(
            Calculation.name == calc_name
        ).first()
        
        if not calc:
            raise ValueError(f"Calculation '{calc_name}' not found")
        
        calc.is_active = False
        self.config_db.commit()
        return True

    async def get_available_deals(self) -> List[Dict[str, Any]]:
        """Get list of available deals from data warehouse"""
        deals = self.dw_db.query(Deal.dl_nbr, Deal.issr_cde, Deal.cdi_file_nme).all()
        return [
            {
                "dl_nbr": deal.dl_nbr,
                "issr_cde": deal.issr_cde,
                "cdi_file_nme": deal.cdi_file_nme
            }
            for deal in deals
        ]
    
    async def get_available_tranches(self, deal_numbers: List[int] = None) -> List[Dict[str, Any]]:
        """Get list of available tranches from data warehouse"""
        query = self.dw_db.query(Tranche.tr_id, Tranche.tr_cusip_id, Tranche.dl_nbr)
        
        if deal_numbers:
            query = query.filter(Tranche.dl_nbr.in_(deal_numbers))
        
        tranches = query.all()
        return [
            {
                "tr_id": tranche.tr_id,
                "tr_cusip_id": tranche.tr_cusip_id,
                "dl_nbr": tranche.dl_nbr
            }
            for tranche in tranches
        ]
    
    async def get_available_cycles(self) -> List[Dict[str, Any]]:
        """Get list of available cycle codes from data warehouse"""
        cycles = self.dw_db.query(TrancheBal.cycle_cde).distinct().order_by(TrancheBal.cycle_cde.desc()).all()
        return [{"cycle_cde": cycle.cycle_cde} for cycle in cycles]
    
    async def _log_execution(
        self, 
        report_name: str, 
        user_id: str, 
        execution_time: float, 
        row_count: int, 
        parameters: dict, 
        success: bool, 
        error_message: str = None
    ):
        """Log report execution to config database"""
        log_entry = ReportExecutionLog(
            report_name=report_name,
            executed_by=user_id,
            execution_time_ms=execution_time,
            row_count=row_count,
            parameters=parameters,
            success=success,
            error_message=error_message
        )
        
        self.config_db.add(log_entry)
        self.config_db.commit()