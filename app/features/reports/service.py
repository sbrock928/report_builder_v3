# app/features/reports/service.py
"""Refactored report service using unified query engine"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import time

from app.core.exceptions import ReportGenerationError
from app.features.calculations.models import Calculation
from app.shared.query_engine import QueryEngine
from .models import Report, ReportDeal, ReportTranche, ReportCalculation, ReportExecutionLog
from .schemas import (
    ReportCreateRequest, ReportUpdateRequest, ReportExecuteRequest,
    ReportResponse, ReportTemplateResponse, ReportTemplateDetailResponse
)
from .repository import ReportRepository

class ReportService:
    """Streamlined report service using unified query engine"""
    
    def __init__(self, config_db: Session, query_engine: QueryEngine):
        self.config_db = config_db
        self.query_engine = query_engine
        self.repository = ReportRepository(config_db)
    
    async def create_report_template(self, request: ReportCreateRequest, user_id: str = "api_user") -> ReportTemplateDetailResponse:
        """Create a new report template"""
        
        # Validate calculations exist using query engine
        calculations = self.query_engine.get_calculations_by_names(request.selected_calculations)
        
        if len(calculations) != len(request.selected_calculations):
            found_names = {calc.name for calc in calculations}
            missing = set(request.selected_calculations) - found_names
            raise ReportGenerationError(f"Calculations not found: {', '.join(missing)}")
        
        # Create report
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
        """Get detailed report template configuration"""
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
        """Update an existing report template"""
        report = self.config_db.query(Report).filter(
            Report.id == report_id,
            Report.is_active == True
        ).first()
        
        if not report:
            raise ReportGenerationError(f"Report template {report_id} not found")
        
        # Update basic fields
        if request.name is not None:
            report.name = request.name
        if request.description is not None:
            report.description = request.description
        
        # Update deals if provided
        if request.selected_deals is not None:
            self.config_db.query(ReportDeal).filter(ReportDeal.report_id == report_id).delete()
            for deal_num in request.selected_deals:
                report_deal = ReportDeal(report_id=report_id, deal_number=deal_num)
                self.config_db.add(report_deal)
        
        # Update tranches if provided
        if request.selected_tranches is not None:
            self.config_db.query(ReportTranche).filter(ReportTranche.report_id == report_id).delete()
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
            self.config_db.query(ReportCalculation).filter(ReportCalculation.report_id == report_id).delete()
            
            # Validate calculations exist using query engine
            calculations = self.query_engine.get_calculations_by_names(request.selected_calculations)
            
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
        """Execute a report template using unified query engine"""
        start_time = time.time()
        
        try:
            # Load report template
            report = self.config_db.query(Report).filter(
                Report.id == report_id,
                Report.is_active == True
            ).first()
            
            if not report:
                raise ReportGenerationError(f"Report template {report_id} not found")
            
            # Get report configuration
            deal_numbers = [rd.deal_number for rd in report.report_deals]
            tranche_ids = [rt.tranche_id for rt in report.report_tranches]
            cycle_code = request.cycle_code
            
            # Load calculations ordered by display_order
            report_calculations = self.config_db.query(ReportCalculation).filter(
                ReportCalculation.report_id == report_id
            ).order_by(ReportCalculation.display_order).all()
            
            calculations = []
            for rc in report_calculations:
                calc = self.config_db.query(Calculation).filter(Calculation.id == rc.calculation_id).first()
                if calc:
                    calculations.append(calc)
            
            # Execute report using unified query engine
            results = self.query_engine.execute_report_query(
                deal_numbers=deal_numbers,
                tranche_ids=tranche_ids,
                cycle_code=cycle_code,
                calculations=calculations,
                aggregation_level=report.aggregation_level
            )
            
            # Process results using query engine
            data = self.query_engine.process_report_results(
                results=results,
                calculations=calculations,
                aggregation_level=report.aggregation_level
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Log successful execution
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
            
            # Log failed execution
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
    
    async def preview_report_sql(self, report_id: int, cycle_code: int) -> Dict[str, Any]:
        """Preview SQL using unified query engine"""
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
        for rc in report_calculations:
            calc = self.config_db.query(Calculation).filter(Calculation.id == rc.calculation_id).first()
            if calc:
                calculations.append(calc)
        
        # Use unified query engine for preview
        return self.query_engine.preview_report_sql(
            report_name=report.name,
            aggregation_level=report.aggregation_level,
            deal_numbers=deal_numbers,
            tranche_ids=tranche_ids,
            cycle_code=cycle_code,
            calculations=calculations
        )

    async def get_execution_logs(self, report_id: int, limit: int = 50) -> List[dict]:
        """Get execution logs for a report template"""
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
                "cycle_code": log.cycle_code,
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
        cycle_code: int,
        executed_by: str,
        execution_time_ms: float,
        row_count: int,
        success: bool,
        error_message: str = None
    ):
        """Log report execution"""
        log_entry = ReportExecutionLog(
            report_id=report_id,
            cycle_code=cycle_code,
            executed_by=executed_by,
            execution_time_ms=execution_time_ms,
            row_count=row_count,
            success=success,
            error_message=error_message
        )
        
        self.config_db.add(log_entry)
        self.config_db.commit()
    
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