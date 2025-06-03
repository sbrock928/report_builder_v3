# app/features/reports/service.py
"""Updated service with cycle_code moved to execution time"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from app.core.exceptions import ReportGenerationError
from app.features.calculations.service import CalculationNotFoundError
from app.features.datawarehouse.models import Deal, Tranche, TrancheBal
from app.features.calculations.models import Calculation, SourceModel, AggregationFunction
from .models import Report, ReportDeal, ReportTranche, ReportCalculation, ReportExecutionLog
from .schemas import (
    ReportCreateRequest, ReportUpdateRequest, ReportExecuteRequest,
    ReportResponse, ReportRow, ReportTemplateResponse, ReportTemplateDetailResponse
)
from .repository import ReportRepository

class ReportService:
    """Updated service for template-based reports with runtime cycle selection"""
    
    def __init__(self, dw_db: Session, config_db: Session):
        self.dw_db = dw_db
        self.config_db = config_db
        self.repository = ReportRepository(config_db)
    
    async def create_report_template(self, request: ReportCreateRequest, user_id: str = "api_user") -> ReportTemplateDetailResponse:
        """Create a new report template (no cycle_code stored)"""
        
        # Validate calculations exist
        calculations = self.config_db.query(Calculation).filter(
            Calculation.name.in_(request.selected_calculations),
            Calculation.is_active == True
        ).all()
        
        if len(calculations) != len(request.selected_calculations):
            found_names = {calc.name for calc in calculations}
            missing = set(request.selected_calculations) - found_names
            raise ReportGenerationError(f"Calculations not found: {', '.join(missing)}")
        
        # Create report (no cycle_code)
        report = Report(
            name=request.name,
            description=request.description,
            aggregation_level=request.aggregation_level.value,
            created_by=user_id
        )
        self.config_db.add(report)
        self.config_db.flush()  # Get the ID
        
        # Add deals
        for deal_num in request.selected_deals:
            report_deal = ReportDeal(report_id=report.id, deal_number=deal_num)
            self.config_db.add(report_deal)
        
        # Add tranches
        for tranche_id in request.selected_tranches:
            for deal_num in request.selected_deals:
                report_tranche = ReportTranche(
                    report_id=report.id,
                    deal_number=deal_num,
                    tranche_id=tranche_id
                )
                self.config_db.add(report_tranche)
        
        # Add calculations
        for i, calc in enumerate(calculations):
            report_calc = ReportCalculation(
                report_id=report.id,
                calculation_id=calc.id,
                display_order=i
            )
            self.config_db.add(report_calc)
        
        self.config_db.commit()
        self.config_db.refresh(report)
        
        return await self.get_report_template_detail(report.id)
    
    async def get_report_templates(self) -> List[ReportTemplateResponse]:
        """Get list of all report templates with execution history"""
        reports = self.config_db.query(Report).filter(Report.is_active == True).all()
        
        result = []
        for report in reports:
            # Get most recent execution
            last_execution = self.config_db.query(ReportExecutionLog)\
                .filter(ReportExecutionLog.report_id == report.id)\
                .order_by(ReportExecutionLog.executed_at.desc())\
                .first()
            
            result.append(ReportTemplateResponse(
                id=report.id,
                name=report.name,
                description=report.description,
                aggregation_level=report.aggregation_level,
                deal_count=len(report.report_deals),
                tranche_count=len(report.report_tranches),
                calculation_count=len(report.report_calculations),
                last_executed_cycle=last_execution.cycle_code if last_execution else None,
                created_at=report.created_at,
                updated_at=report.updated_at,
                created_by=report.created_by
            ))
        
        return result
    
    async def get_report_template_detail(self, report_id: int) -> ReportTemplateDetailResponse:
        """Get detailed report template configuration with recent executions"""
        report = self.config_db.query(Report).filter(
            Report.id == report_id,
            Report.is_active == True
        ).first()
        
        if not report:
            raise ReportGenerationError(f"Report template {report_id} not found")
        
        # Get selected deals, tranches, and calculations
        deal_numbers = [rd.deal_number for rd in report.report_deals]
        tranche_ids = list(set(rt.tranche_id for rt in report.report_tranches))
        
        # Get calculations ordered by display_order
        report_calculations = self.config_db.query(ReportCalculation).filter(
            ReportCalculation.report_id == report_id
        ).order_by(ReportCalculation.display_order).all()
        
        calculation_names = []
        for rc in report_calculations:
            calc = self.config_db.query(Calculation).filter(Calculation.id == rc.calculation_id).first()
            if calc:
                calculation_names.append(calc.name)
        
        # Get recent executions
        recent_executions = self.config_db.query(ReportExecutionLog)\
            .filter(ReportExecutionLog.report_id == report_id)\
            .order_by(ReportExecutionLog.executed_at.desc())\
            .limit(5).all()
        
        recent_exec_data = [
            {
                "cycle_code": exec_log.cycle_code,
                "executed_at": exec_log.executed_at,
                "success": exec_log.success,
                "row_count": exec_log.row_count,
                "execution_time_ms": exec_log.execution_time_ms
            }
            for exec_log in recent_executions
        ]
        
        return ReportTemplateDetailResponse(
            id=report.id,
            name=report.name,
            description=report.description,
            aggregation_level=report.aggregation_level,
            selected_deals=deal_numbers,
            selected_tranches=tranche_ids,
            selected_calculations=calculation_names,
            recent_executions=recent_exec_data,
            created_at=report.created_at,
            updated_at=report.updated_at,
            created_by=report.created_by
        )
    
    async def update_report_template(self, report_id: int, request: ReportUpdateRequest) -> ReportTemplateDetailResponse:
        """Update an existing report template (no cycle_code updates)"""
        report = self.config_db.query(Report).filter(
            Report.id == report_id,
            Report.is_active == True
        ).first()
        
        if not report:
            raise ReportGenerationError(f"Report template {report_id} not found")
        
        # Update basic fields (no cycle_code)
        if request.name is not None:
            report.name = request.name
        if request.description is not None:
            report.description = request.description
        
        # Update deals if provided
        if request.selected_deals is not None:
            # Delete existing deals
            self.config_db.query(ReportDeal).filter(ReportDeal.report_id == report_id).delete()
            
            # Add new deals
            for deal_num in request.selected_deals:
                report_deal = ReportDeal(report_id=report_id, deal_number=deal_num)
                self.config_db.add(report_deal)
        
        # Update tranches if provided
        if request.selected_tranches is not None:
            # Delete existing tranches
            self.config_db.query(ReportTranche).filter(ReportTranche.report_id == report_id).delete()
            
            # Add new tranches (use existing or updated deals)
            deal_numbers = request.selected_deals if request.selected_deals is not None else [rd.deal_number for rd in report.report_deals]
            for tranche_id in request.selected_tranches:
                for deal_num in deal_numbers:
                    report_tranche = ReportTranche(
                        report_id=report_id,
                        deal_number=deal_num,
                        tranche_id=tranche_id
                    )
                    self.config_db.add(report_tranche)
        
        # Update calculations if provided
        if request.selected_calculations is not None:
            # Delete existing calculations
            self.config_db.query(ReportCalculation).filter(ReportCalculation.report_id == report_id).delete()
            
            # Validate calculations exist
            calculations = self.config_db.query(Calculation).filter(
                Calculation.name.in_(request.selected_calculations),
                Calculation.is_active == True
            ).all()
            
            if len(calculations) != len(request.selected_calculations):
                found_names = {calc.name for calc in calculations}
                missing = set(request.selected_calculations) - found_names
                raise ReportGenerationError(f"Calculations not found: {', '.join(missing)}")
            
            # Add new calculations
            for i, calc in enumerate(calculations):
                report_calc = ReportCalculation(
                    report_id=report_id,
                    calculation_id=calc.id,
                    display_order=i
                )
                self.config_db.add(report_calc)
        
        self.config_db.commit()
        self.config_db.refresh(report)
        
        return await self.get_report_template_detail(report_id)
    
    async def execute_report(self, report_id: int, request: ReportExecuteRequest, user_id: str = "api_user") -> ReportResponse:
        """Execute a report template with specified cycle_code"""
        start_time = time.time()
        
        try:
            # Load report template
            report = self.config_db.query(Report).filter(
                Report.id == report_id,
                Report.is_active == True
            ).first()
            
            if not report:
                raise ReportGenerationError(f"Report template {report_id} not found")
            
            # cycle_code comes from request (required)
            cycle_code = request.cycle_code
            
            # Load report configuration
            deal_numbers = [rd.deal_number for rd in report.report_deals]
            tranche_ids = [rt.tranche_id for rt in report.report_tranches]
            
            # Load calculations ordered by display_order
            report_calculations = self.config_db.query(ReportCalculation).filter(
                ReportCalculation.report_id == report_id
            ).order_by(ReportCalculation.display_order).all()
            
            calculations = []
            for rc in report_calculations:
                calc = self.config_db.query(Calculation).filter(Calculation.id == rc.calculation_id).first()
                if calc:
                    calculations.append(calc)
            
            # Generate report data using ORM with LEFT JOINs
            if report.aggregation_level == "tranche":
                data = await self._execute_tranche_level_report(
                    deal_numbers, tranche_ids, cycle_code, calculations
                )
            else:
                data = await self._execute_deal_level_report(
                    deal_numbers, tranche_ids, cycle_code, calculations
                )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Log successful execution (with cycle_code)
            await self._log_execution(
                report_id=report_id,
                cycle_code=cycle_code,
                executed_by=user_id,
                execution_time_ms=execution_time,
                row_count=len(data),
                success=True
            )
            
            return ReportResponse(
                report_id=report_id,
                report_name=report.name,
                aggregation_level=report.aggregation_level,
                cycle_code=cycle_code,
                generated_at=datetime.now(),
                row_count=len(data),
                columns=[calc.name for calc in calculations],
                data=data,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            # Log failed execution (with cycle_code)
            await self._log_execution(
                report_id=report_id,
                cycle_code=request.cycle_code,
                executed_by=user_id,
                execution_time_ms=execution_time,
                row_count=0,
                success=False,
                error_message=str(e)
            )
            
            raise ReportGenerationError(f"Report execution failed: {str(e)}")
    
    # app/features/reports/service.py
    async def _execute_deal_level_report(
        self, 
        deal_numbers: List[int], 
        tranche_ids: List[str], 
        cycle_code: int, 
        calculations: List[Calculation]
    ) -> List[ReportRow]:
        """Execute deal-level report using ORM with proper JOIN order"""
        
        # Start with base query - get all deals and cycle combinations that exist
        base_results = self.dw_db.query(
            Deal.dl_nbr,
            TrancheBal.cycle_cde
        ).join(Tranche, Deal.dl_nbr == Tranche.dl_nbr)\
        .join(TrancheBal, and_(
            Tranche.dl_nbr == TrancheBal.dl_nbr,
            Tranche.tr_id == TrancheBal.tr_id
        ))\
        .filter(Deal.dl_nbr.in_(deal_numbers))\
        .filter(Tranche.tr_id.in_(tranche_ids))\
        .filter(TrancheBal.cycle_cde == cycle_code)\
        .distinct().all()
        
        # Calculate each metric separately and combine results
        data = []
        for deal_nbr, cycle in base_results:
            values = {}
            
            for calc in calculations:
                try:
                    # Build query starting from Deal with proper join structure
                    query = self.dw_db.query(calc.get_sqlalchemy_function()).select_from(Deal)
                    
                    # Add required joins based on calculation's source model
                    required_models = calc.get_required_models()
                    
                    if Tranche in required_models:
                        query = query.join(Tranche, Deal.dl_nbr == Tranche.dl_nbr)
                    
                    if TrancheBal in required_models:
                        query = query.join(TrancheBal, and_(
                            Tranche.dl_nbr == TrancheBal.dl_nbr,
                            Tranche.tr_id == TrancheBal.tr_id
                        ))
                    
                    # Apply filters
                    result = query.filter(Deal.dl_nbr == deal_nbr)\
                        .filter(Tranche.tr_id.in_(tranche_ids))\
                        .filter(TrancheBal.cycle_cde == cycle)\
                        .scalar()
                    
                    values[calc.name] = result
                except Exception as e:
                    print(f"Error calculating {calc.name} for deal {deal_nbr}: {e}")
                    values[calc.name] = None
            
            data.append(ReportRow(
                dl_nbr=deal_nbr,
                cycle_cde=cycle,
                values=values
            ))
        
        return data

    async def _execute_tranche_level_report(
        self, 
        deal_numbers: List[int], 
        tranche_ids: List[str], 
        cycle_code: int, 
        calculations: List[Calculation]
    ) -> List[ReportRow]:
        """Execute tranche-level report using ORM with proper JOIN order"""
        
        # Get all tranche/cycle combinations that exist
        base_results = self.dw_db.query(
            Deal.dl_nbr,
            Tranche.tr_id,
            TrancheBal.cycle_cde
        ).join(Tranche, Deal.dl_nbr == Tranche.dl_nbr)\
        .join(TrancheBal, and_(
            Tranche.dl_nbr == TrancheBal.dl_nbr,
            Tranche.tr_id == TrancheBal.tr_id
        ))\
        .filter(Deal.dl_nbr.in_(deal_numbers))\
        .filter(Tranche.tr_id.in_(tranche_ids))\
        .filter(TrancheBal.cycle_cde == cycle_code)\
        .distinct().all()
        
        # Calculate each metric separately and combine results
        data = []
        for deal_nbr, tranche_id, cycle in base_results:
            values = {}
            
            for calc in calculations:
                try:
                    # Build query starting from Deal with proper join structure
                    query = self.dw_db.query(calc.get_sqlalchemy_function()).select_from(Deal)
                    
                    # Add required joins based on calculation's source model
                    required_models = calc.get_required_models()
                    
                    if Tranche in required_models:
                        query = query.join(Tranche, Deal.dl_nbr == Tranche.dl_nbr)
                    
                    if TrancheBal in required_models:
                        query = query.join(TrancheBal, and_(
                            Tranche.dl_nbr == TrancheBal.dl_nbr,
                            Tranche.tr_id == TrancheBal.tr_id
                        ))
                    
                    # Apply filters
                    result = query.filter(Deal.dl_nbr == deal_nbr)\
                        .filter(Tranche.tr_id == tranche_id)\
                        .filter(TrancheBal.cycle_cde == cycle)\
                        .scalar()
                    
                    values[calc.name] = result
                except Exception as e:
                    print(f"Error calculating {calc.name} for deal {deal_nbr}, tranche {tranche_id}: {e}")
                    values[calc.name] = None
            
            data.append(ReportRow(
                dl_nbr=deal_nbr,
                tr_id=tranche_id,
                cycle_cde=cycle,
                values=values
            ))
        
        return data
    
    async def get_execution_logs(self, report_id: int, limit: int = 50) -> List[dict]:
        """Get execution logs for a report template (now includes cycle_code)"""
        report = self.config_db.query(Report).filter(
            Report.id == report_id,
            Report.is_active == True
        ).first()
        
        if not report:
            raise ReportGenerationError(f"Report template {report_id} not found")
        
        logs = self.repository.get_execution_logs(report_id, limit)
        
        return [
            {
                "id": log.id,
                "cycle_code": log.cycle_code,  # Now included
                "executed_by": log.executed_by,
                "execution_time_ms": log.execution_time_ms,
                "row_count": log.row_count,
                "success": log.success,
                "error_message": log.error_message,
                "executed_at": log.executed_at
            }
            for log in logs
        ]
    
    async def _log_execution(
        self,
        report_id: int,
        cycle_code: int,  # Now required
        executed_by: str,
        execution_time_ms: float,
        row_count: int,
        success: bool,
        error_message: str = None
    ):
        """Log report execution (with cycle_code)"""
        log_entry = ReportExecutionLog(
            report_id=report_id,
            cycle_code=cycle_code,  # Store cycle in execution log
            executed_by=executed_by,
            execution_time_ms=execution_time_ms,
            row_count=row_count,
            success=success,
            error_message=error_message
        )
        
        self.config_db.add(log_entry)
        self.config_db.commit()
    
    async def delete_calculation(self, calc_id: int) -> dict:
        """Delete a calculation (soft delete)"""
        calculation = self.repository.get_by_id(calc_id)
        if not calculation:
            raise CalculationNotFoundError(f"Calculation with ID {calc_id} not found")
        
        self.repository.soft_delete(calculation)
        return {"message": f"Calculation '{calculation.name}' deleted successfully"}
    
    async def preview_report_sql(self, report_id: int, cycle_code: int, use_simple_query: bool = False) -> Dict[str, Any]:
        """Preview SQL that would be generated for this report template using the same ORM method as execution"""
        # Load report template
        report = self.config_db.query(Report).filter(
            Report.id == report_id,
            Report.is_active == True
        ).first()
        
        if not report:
            raise ReportGenerationError(f"Report template {report_id} not found")
        
        # Get report configuration
        deal_numbers = [rd.deal_number for rd in report.report_deals]
        tranche_ids = list(set(rt.tranche_id for rt in report.report_tranches))
        
        # Load calculations ordered by display_order
        report_calculations = self.config_db.query(ReportCalculation).filter(
            ReportCalculation.report_id == report_id
        ).order_by(ReportCalculation.display_order).all()
        
        calculations = []
        calc_details = []
        for rc in report_calculations:
            calc = self.config_db.query(Calculation).filter(Calculation.id == rc.calculation_id).first()
            if calc:
                calculations.append(calc)
                # Store calculation details for response
                calc_details.append({
                    'name': calc.name,
                    'aggregation_function': calc.aggregation_function.value,
                    'source_model': calc.source_model.value,
                    'source_field': calc.source_field,
                    'weight_field': calc.weight_field,
                    'group_level': calc.group_level.value
                })
        
        # Generate the actual ORM query that would be used for execution
        if report.aggregation_level == "deal":
            sql_query = self._generate_orm_deal_level_query(deal_numbers, tranche_ids, cycle_code, calculations)
        else:
            sql_query = self._generate_orm_tranche_level_query(deal_numbers, tranche_ids, cycle_code, calculations)
        
        # Estimate complexity and rows
        query_complexity = "Medium"
        if len(calculations) > 5 or len(deal_numbers) > 20:
            query_complexity = "High"
        elif len(calculations) <= 2 and len(deal_numbers) <= 5:
            query_complexity = "Low"
        
        estimated_rows = len(deal_numbers) if report.aggregation_level == "deal" else len(deal_numbers) * len(tranche_ids)
        
        return {
            "template_name": report.name,
            "aggregation_level": report.aggregation_level,
            "sample_cycle": cycle_code,
            "deal_count": len(deal_numbers),
            "tranche_count": len(tranche_ids),
            "calculation_count": len(calculations),
            "sql_query": sql_query,
            "parameters": {
                "cycle_code": cycle_code,
                "deal_numbers": deal_numbers,
                "tranche_ids": tranche_ids
            },
            "selected_calculations": calc_details,
            "query_complexity": query_complexity,
            "estimated_rows": estimated_rows
        }
    
    def _generate_orm_deal_level_query(self, deal_numbers: List[int], tranche_ids: List[str], cycle_code: int, calculations: List[Calculation]) -> str:
        """Generate a single consolidated SQL query that LEFT JOINs all calculations"""
        from sqlalchemy import and_, case, literal_column
        
        # Start with the base query structure
        base_query = self.dw_db.query(
            Deal.dl_nbr.label('deal_number'),
            TrancheBal.cycle_cde.label('cycle_code')
        ).select_from(Deal)\
        .join(Tranche, Deal.dl_nbr == Tranche.dl_nbr)\
        .join(TrancheBal, and_(
            Tranche.dl_nbr == TrancheBal.dl_nbr,
            Tranche.tr_id == TrancheBal.tr_id
        ))
        
        # Add each calculation as a column using subquery approach
        for calc in calculations:
            # Create subquery for this calculation
            calc_subquery = self.dw_db.query(
                Deal.dl_nbr.label('calc_deal_nbr'),
                calc.get_sqlalchemy_function().label(f'{calc.name.lower().replace(" ", "_")}')
            ).select_from(Deal)
            
            # Add required joins based on calculation's source model
            required_models = calc.get_required_models()
            
            if Tranche in required_models:
                calc_subquery = calc_subquery.join(Tranche, Deal.dl_nbr == Tranche.dl_nbr)
            
            if TrancheBal in required_models:
                calc_subquery = calc_subquery.join(TrancheBal, and_(
                    Tranche.dl_nbr == TrancheBal.dl_nbr,
                    Tranche.tr_id == TrancheBal.tr_id
                ))
            
            # Apply filters and group by deal
            calc_subquery = calc_subquery.filter(Deal.dl_nbr.in_(deal_numbers))\
                .filter(Tranche.tr_id.in_(tranche_ids))\
                .filter(TrancheBal.cycle_cde == cycle_code)\
                .group_by(Deal.dl_nbr)\
                .subquery()
            
            # LEFT JOIN this calculation to the base query
            base_query = base_query.outerjoin(
                calc_subquery, 
                Deal.dl_nbr == calc_subquery.c.calc_deal_nbr
            ).add_columns(calc_subquery.c[f'{calc.name.lower().replace(" ", "_")}'].label(calc.name))
        
        # Apply base filters and group by
        final_query = base_query.filter(Deal.dl_nbr.in_(deal_numbers))\
            .filter(Tranche.tr_id.in_(tranche_ids))\
            .filter(TrancheBal.cycle_cde == cycle_code)\
            .group_by(Deal.dl_nbr, TrancheBal.cycle_cde)\
            .distinct()
        
        # Compile to SQL
        compiled_sql = str(final_query.statement.compile(
            dialect=self.dw_db.bind.dialect, 
            compile_kwargs={"literal_binds": True}
        ))
        
        return f"""-- Consolidated report query with all calculations LEFT JOINed:
{compiled_sql}

-- This single query retrieves all deal-level metrics in one execution,
-- using LEFT JOINs to ensure all deals appear even if some calculations return NULL."""
    
    def _generate_orm_tranche_level_query(self, deal_numbers: List[int], tranche_ids: List[str], cycle_code: int, calculations: List[Calculation]) -> str:
        """Generate a single consolidated SQL query that LEFT JOINs all calculations"""
        from sqlalchemy import and_, case, literal_column
        
        # Start with the base query structure
        base_query = self.dw_db.query(
            Deal.dl_nbr.label('deal_number'),
            Tranche.tr_id.label('tranche_id'),
            TrancheBal.cycle_cde.label('cycle_code')
        ).select_from(Deal)\
        .join(Tranche, Deal.dl_nbr == Tranche.dl_nbr)\
        .join(TrancheBal, and_(
            Tranche.dl_nbr == TrancheBal.dl_nbr,
            Tranche.tr_id == TrancheBal.tr_id
        ))
        
        # Add each calculation as a column using subquery approach
        for calc in calculations:
            # Create subquery for this calculation
            calc_subquery = self.dw_db.query(
                Deal.dl_nbr.label('calc_deal_nbr'),
                Tranche.tr_id.label('calc_tranche_id'),
                calc.get_sqlalchemy_function().label(f'{calc.name.lower().replace(" ", "_")}')
            ).select_from(Deal)
            
            # Add required joins based on calculation's source model
            required_models = calc.get_required_models()
            
            if Tranche in required_models:
                calc_subquery = calc_subquery.join(Tranche, Deal.dl_nbr == Tranche.dl_nbr)
            
            if TrancheBal in required_models:
                calc_subquery = calc_subquery.join(TrancheBal, and_(
                    Tranche.dl_nbr == TrancheBal.dl_nbr,
                    Tranche.tr_id == TrancheBal.tr_id
                ))
            
            # Apply filters and group by deal/tranche
            calc_subquery = calc_subquery.filter(Deal.dl_nbr.in_(deal_numbers))\
                .filter(Tranche.tr_id.in_(tranche_ids))\
                .filter(TrancheBal.cycle_cde == cycle_code)\
                .group_by(Deal.dl_nbr, Tranche.tr_id)\
                .subquery()
            
            # LEFT JOIN this calculation to the base query
            base_query = base_query.outerjoin(
                calc_subquery, 
                and_(
                    Deal.dl_nbr == calc_subquery.c.calc_deal_nbr,
                    Tranche.tr_id == calc_subquery.c.calc_tranche_id
                )
            ).add_columns(calc_subquery.c[f'{calc.name.lower().replace(" ", "_")}'].label(calc.name))
        
        # Apply base filters and group by
        final_query = base_query.filter(Deal.dl_nbr.in_(deal_numbers))\
            .filter(Tranche.tr_id.in_(tranche_ids))\
            .filter(TrancheBal.cycle_cde == cycle_code)\
            .group_by(Deal.dl_nbr, Tranche.tr_id, TrancheBal.cycle_cde)\
            .distinct()
        
        # Compile to SQL
        compiled_sql = str(final_query.statement.compile(
            dialect=self.dw_db.bind.dialect, 
            compile_kwargs={"literal_binds": True}
        ))
        
        return f"""-- Consolidated report query with all calculations LEFT JOINed:
{compiled_sql}

-- This single query retrieves all tranche-level metrics in one execution,
-- using LEFT JOINs to ensure all tranches appear even if some calculations return NULL."""
    
    async def delete_report_template(self, report_id: int) -> dict:
        """Delete a report template (soft delete)"""
        report = self.config_db.query(Report).filter(
            Report.id == report_id,
            Report.is_active == True
        ).first()
        
        if not report:
            raise ReportGenerationError(f"Report template {report_id} not found")
        
        # Soft delete
        report.is_active = False
        self.config_db.commit()
        
        return {"message": f"Report template '{report.name}' deleted successfully"}