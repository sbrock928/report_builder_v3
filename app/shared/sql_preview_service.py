# app/shared/sql_preview_service.py
"""Shared SQL preview service for both calculations and reports"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Dict, Any, Optional
from app.features.datawarehouse.models import Deal, Tranche, TrancheBal
from app.features.calculations.models import Calculation


class SqlPreviewService:
    """Shared service for generating SQL previews using the same ORM logic as execution"""
    
    def __init__(self, dw_db: Session, config_db: Session):
        self.dw_db = dw_db
        self.config_db = config_db
    
    def build_consolidated_query(
        self, 
        deal_numbers: List[int], 
        tranche_ids: List[str], 
        cycle_code: int, 
        calculations: List[Calculation], 
        aggregation_level: str
    ):
        """Build the consolidated ORM query used by both preview and execution"""
        
        # Start with the base query structure
        if aggregation_level == "tranche":
            base_query = self.dw_db.query(
                Deal.dl_nbr.label('deal_number'),
                Tranche.tr_id.label('tranche_id'),
                TrancheBal.cycle_cde.label('cycle_code')
            )
        else:
            base_query = self.dw_db.query(
                Deal.dl_nbr.label('deal_number'),
                TrancheBal.cycle_cde.label('cycle_code')
            )
        
        base_query = base_query.select_from(Deal)\
            .join(Tranche, Deal.dl_nbr == Tranche.dl_nbr)\
            .join(TrancheBal, and_(
                Tranche.dl_nbr == TrancheBal.dl_nbr,
                Tranche.tr_id == TrancheBal.tr_id
            ))
        
        # Add each calculation as a column using subquery approach
        for calc in calculations:
            # Create subquery for this calculation
            if aggregation_level == "tranche":
                calc_subquery = self.dw_db.query(
                    Deal.dl_nbr.label('calc_deal_nbr'),
                    Tranche.tr_id.label('calc_tranche_id'),
                    calc.get_sqlalchemy_function().label(f'{calc.name.lower().replace(" ", "_").replace("-", "_")}')
                )
            else:
                calc_subquery = self.dw_db.query(
                    Deal.dl_nbr.label('calc_deal_nbr'),
                    calc.get_sqlalchemy_function().label(f'{calc.name.lower().replace(" ", "_").replace("-", "_")}')
                )
            
            calc_subquery = calc_subquery.select_from(Deal)
            
            # Add required joins based on calculation's source model
            required_models = calc.get_required_models()
            
            if Tranche in required_models:
                calc_subquery = calc_subquery.join(Tranche, Deal.dl_nbr == Tranche.dl_nbr)
            
            if TrancheBal in required_models:
                calc_subquery = calc_subquery.join(TrancheBal, and_(
                    Tranche.dl_nbr == TrancheBal.dl_nbr,
                    Tranche.tr_id == TrancheBal.tr_id
                ))
            
            # Apply filters and group by
            calc_subquery = calc_subquery.filter(Deal.dl_nbr.in_(deal_numbers))\
                .filter(Tranche.tr_id.in_(tranche_ids))\
                .filter(TrancheBal.cycle_cde == cycle_code)
            
            if aggregation_level == "tranche":
                calc_subquery = calc_subquery.group_by(Deal.dl_nbr, Tranche.tr_id)
            else:
                calc_subquery = calc_subquery.group_by(Deal.dl_nbr)
            
            calc_subquery = calc_subquery.subquery()
            
            # LEFT JOIN this calculation to the base query
            if aggregation_level == "tranche":
                base_query = base_query.outerjoin(
                    calc_subquery, 
                    and_(
                        Deal.dl_nbr == calc_subquery.c.calc_deal_nbr,
                        Tranche.tr_id == calc_subquery.c.calc_tranche_id
                    )
                )
            else:
                base_query = base_query.outerjoin(
                    calc_subquery, 
                    Deal.dl_nbr == calc_subquery.c.calc_deal_nbr
                )
            
            # Add the calculation column
            column_name = f'{calc.name.lower().replace(" ", "_").replace("-", "_")}'
            base_query = base_query.add_columns(calc_subquery.c[column_name].label(calc.name))
        
        # Apply base filters and group by
        final_query = base_query.filter(Deal.dl_nbr.in_(deal_numbers))\
            .filter(Tranche.tr_id.in_(tranche_ids))\
            .filter(TrancheBal.cycle_cde == cycle_code)
        
        if aggregation_level == "tranche":
            final_query = final_query.group_by(Deal.dl_nbr, Tranche.tr_id, TrancheBal.cycle_cde)
        else:
            final_query = final_query.group_by(Deal.dl_nbr, TrancheBal.cycle_cde)
        
        return final_query.distinct()
    
    def preview_calculation_sql(
        self,
        calculation: Calculation,
        aggregation_level: str = "deal",
        sample_deals: List[int] = None,
        sample_tranches: List[str] = None,
        sample_cycle: int = None
    ) -> Dict[str, Any]:
        """Generate SQL preview for a single calculation using the same ORM logic"""
        
        # Use default sample data if not provided
        if sample_deals is None:
            sample_deals = [101, 102, 103]
        if sample_tranches is None:
            sample_tranches = ["A", "B"]
        if sample_cycle is None:
            sample_cycle = 202404
        
        # Build query for just this one calculation
        query = self.build_consolidated_query(
            deal_numbers=sample_deals,
            tranche_ids=sample_tranches, 
            cycle_code=sample_cycle,
            calculations=[calculation],
            aggregation_level=aggregation_level
        )
        
        # Compile to SQL
        compiled_sql = str(query.statement.compile(
            dialect=self.dw_db.bind.dialect, 
            compile_kwargs={"literal_binds": True}
        ))
        
        return {
            "calculation_name": calculation.name,
            "description": calculation.description,
            "aggregation_level": aggregation_level,
            "sample_parameters": {
                "deals": sample_deals,
                "tranches": sample_tranches,
                "cycle": sample_cycle
            },
            "generated_sql": f"""-- CALCULATION PREVIEW (Uses same ORM logic as report execution):
{compiled_sql}

-- This shows how '{calculation.name}' will be calculated when included in reports.
-- The calculation uses {calculation.aggregation_function.value}({calculation.source_model.value}.{calculation.source_field})
-- Group Level: {calculation.group_level.value}""",
            "sql_parameters": {
                "cycle_code": sample_cycle,
                "deal_numbers": sample_deals,
                "tranche_ids": sample_tranches
            },
            "calculation_config": {
                "aggregation_function": calculation.aggregation_function.value,
                "source_model": calculation.source_model.value,
                "source_field": calculation.source_field,
                "group_level": calculation.group_level.value,
                "weight_field": calculation.weight_field
            }
        }
    
    def preview_report_sql(
        self,
        report_name: str,
        aggregation_level: str,
        deal_numbers: List[int],
        tranche_ids: List[str],
        cycle_code: int,
        calculations: List[Calculation]
    ) -> Dict[str, Any]:
        """Generate SQL preview for a full report using the same ORM logic as execution"""
        
        # Build the consolidated query (same as execution)
        query = self.build_consolidated_query(
            deal_numbers=deal_numbers,
            tranche_ids=tranche_ids,
            cycle_code=cycle_code,
            calculations=calculations,
            aggregation_level=aggregation_level
        )
        
        # Compile to SQL
        compiled_sql = str(query.statement.compile(
            dialect=self.dw_db.bind.dialect, 
            compile_kwargs={"literal_binds": True}
        ))
        
        # Estimate complexity and rows
        query_complexity = "Medium"
        if len(calculations) > 5 or len(deal_numbers) > 20:
            query_complexity = "High"
        elif len(calculations) <= 2 and len(deal_numbers) <= 5:
            query_complexity = "Low"
        
        estimated_rows = len(deal_numbers) if aggregation_level == "deal" else len(deal_numbers) * len(tranche_ids)
        
        # Build calculation details
        calc_details = []
        for calc in calculations:
            calc_details.append({
                'name': calc.name,
                'aggregation_function': calc.aggregation_function.value,
                'source_model': calc.source_model.value,
                'source_field': calc.source_field,
                'weight_field': calc.weight_field,
                'group_level': calc.group_level.value
            })
        
        return {
            "template_name": report_name,
            "aggregation_level": aggregation_level,
            "sample_cycle": cycle_code,
            "deal_count": len(deal_numbers),
            "tranche_count": len(tranche_ids),
            "calculation_count": len(calculations),
            "sql_query": f"""-- CONSOLIDATED REPORT QUERY (Used by both preview and execution):
{compiled_sql}

-- This is the exact same query that will be executed when running this report.
-- All calculations are retrieved in a single database round-trip using LEFT JOINs.
-- Query executes {len(calculations)} calculation subqueries joined to the base result set.""",
            "parameters": {
                "cycle_code": cycle_code,
                "deal_numbers": deal_numbers,
                "tranche_ids": tranche_ids
            },
            "selected_calculations": calc_details,
            "query_complexity": query_complexity,
            "estimated_rows": estimated_rows
        }