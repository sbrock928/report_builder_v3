# app/features/reports/builders/query_builder.py
"""Main SQL query builder for reports with optimized LEFT JOINs"""

from typing import List, Dict, Any, Tuple
from .filter_builder import FilterBuilder
import re

class ReportQueryBuilder:
    """Builds optimized SQL queries for report generation"""
    
    def __init__(self, filter_builder: FilterBuilder, subquery_builder=None):
        self.filter_builder = filter_builder
        self.subquery_builder = subquery_builder
    
    def _sanitize_calc_name(self, calc_name: str) -> str:
        """Sanitize calculation name for use as SQL identifier"""
        # Replace spaces and special characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', calc_name)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = f"calc_{sanitized}"
        return sanitized or "calculation"
    
    def build_calculation_subquery(self, calculation: Dict[str, Any], where_clause: str, params: Dict[str, Any]) -> str:
        """Build a subquery for a single calculation with INNER JOINs for proper filtering"""
        
        calc_name = calculation['name']
        sanitized_name = self._sanitize_calc_name(calc_name)
        formula = calculation['formula']
        source_tables = calculation['source_tables']
        group_level = calculation.get('group_level', 'both')
        
        # Determine grouping based on calculation's group_level, not source tables
        if group_level == 'tranche':
            # Tranche-level calculation: group by deal, tranche, and cycle
            group_by_fields = ["d.dl_nbr", "t.tr_id", "tb.cycle_cde"]
        else:
            # Deal-level calculation: group by deal and cycle only
            group_by_fields = ["d.dl_nbr", "tb.cycle_cde"]
        
        # Build FROM clause with INNER JOINs (not LEFT JOINs)
        from_clause = "FROM deal d"
        
        # Add tranche join if needed - INNER JOIN to ensure we only get deals with tranches
        if any(table.startswith('tranche') for table in source_tables):
            from_clause += "\n    INNER JOIN tranche t ON d.dl_nbr = t.dl_nbr"
        
        # Add tranchebal join if needed - INNER JOIN to ensure we only get tranches with balance data
        if any(table.startswith('tranchebal') for table in source_tables):
            from_clause += "\n    INNER JOIN tranchebal tb ON t.dl_nbr = tb.dl_nbr AND t.tr_id = tb.tr_id"
        
        # Build the subquery
        subquery = f"""
        SELECT {', '.join(group_by_fields)},
               {formula} as {sanitized_name}
        {from_clause}
        {where_clause}
        GROUP BY {', '.join(group_by_fields)}
        """
        
        return subquery.strip()
    
    def build_report_query(
        self,
        calculations: List[Dict[str, Any]],
        aggregation_level: str,
        selected_deals: List[int] = None,
        selected_tranches: List[str] = None,
        cycle_code: int = None,
        additional_filters: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Build the main report query with LEFT JOINs of calculation subqueries"""
        
        # Build WHERE clause for filtering
        where_clause, params = self.filter_builder.build_where_clause(
            selected_deals=selected_deals,
            selected_tranches=selected_tranches,
            cycle_code=cycle_code,
            additional_filters=additional_filters
        )
        
        # Determine grouping level - main query uses LEFT JOINs to show all requested deals/tranches
        if aggregation_level == "tranche":
            main_select = "d.dl_nbr, t.tr_id, tb.cycle_cde"
            main_from = """
            FROM deal d
            LEFT JOIN tranche t ON d.dl_nbr = t.dl_nbr
            LEFT JOIN tranchebal tb ON t.dl_nbr = tb.dl_nbr AND t.tr_id = tb.tr_id
            """
            main_group_by = "d.dl_nbr, t.tr_id, tb.cycle_cde"
            # For tranche level, we need to include cycle filtering since we're joining tranchebal
            main_where_clause, main_params = self.filter_builder.build_where_clause(
                selected_deals=selected_deals,
                selected_tranches=selected_tranches,
                cycle_code=cycle_code,  # Include cycle filtering for tranche level
                additional_filters=additional_filters
            )
        else:
            main_select = "d.dl_nbr, tb.cycle_cde"
            main_from = """
            FROM deal d
            LEFT JOIN tranche t ON d.dl_nbr = t.dl_nbr
            LEFT JOIN tranchebal tb ON t.dl_nbr = tb.dl_nbr AND t.tr_id = tb.tr_id
            """
            main_group_by = "d.dl_nbr, tb.cycle_cde"
            # For deal level, we also need cycle filtering since we're joining tranchebal
            main_where_clause, main_params = self.filter_builder.build_where_clause(
                selected_deals=selected_deals,
                selected_tranches=selected_tranches,  # Include tranche filtering to ensure proper joins
                cycle_code=cycle_code,
                additional_filters=additional_filters
            )
        
        # Build main query with LEFT JOINs to calculation subqueries
        select_fields = [main_select]
        join_clauses = []
        
        for calc in calculations:
            calc_name = calc['name']
            sanitized_name = self._sanitize_calc_name(calc_name)
            
            # Add the calculation field to SELECT with original name as alias
            select_fields.append(f"calc_{sanitized_name}.{sanitized_name} as \"{calc_name}\"")
            
            # Create JOIN condition for this calculation - always include cycle_cde
            if aggregation_level == "tranche":
                join_condition = f"d.dl_nbr = calc_{sanitized_name}.dl_nbr AND t.tr_id = calc_{sanitized_name}.tr_id AND tb.cycle_cde = calc_{sanitized_name}.cycle_cde"
            else:
                join_condition = f"d.dl_nbr = calc_{sanitized_name}.dl_nbr AND tb.cycle_cde = calc_{sanitized_name}.cycle_cde"
            
            # Build the subquery (uses INNER JOINs internally)
            subquery = self.build_calculation_subquery(calc, where_clause, params)
            join_clauses.append(f"LEFT JOIN ({subquery}) as calc_{sanitized_name} ON {join_condition}")
        
        # Assemble final query - use main_where_clause for main query
        main_query = f"""
        SELECT {', '.join(select_fields)}
        {main_from}
        {chr(10).join(join_clauses)}
        {main_where_clause}
        GROUP BY {main_group_by}
        ORDER BY d.dl_nbr{', t.tr_id' if aggregation_level == 'tranche' else ''}, tb.cycle_cde
        """
        
        # Use the original params that include cycle filtering for subqueries
        return main_query.strip(), params
    
    def build_simple_aggregation_query(
        self,
        calculations: List[Dict[str, Any]],
        aggregation_level: str,
        selected_deals: List[int] = None,
        selected_tranches: List[str] = None,
        cycle_code: int = None,
        additional_filters: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Build a simpler aggregation query for better performance when possible"""
        
        # Build WHERE clause
        where_clause, params = self.filter_builder.build_where_clause(
            selected_deals=selected_deals,
            selected_tranches=selected_tranches,
            cycle_code=cycle_code,
            additional_filters=additional_filters
        )
        
        # Determine grouping and selection - always include cycle_cde
        if aggregation_level == "tranche":
            select_clause = "d.dl_nbr, t.tr_id, tb.cycle_cde"
            group_by_clause = "d.dl_nbr, t.tr_id, tb.cycle_cde"
            order_by_clause = "d.dl_nbr, t.tr_id, tb.cycle_cde"
        else:
            select_clause = "d.dl_nbr, tb.cycle_cde"
            group_by_clause = "d.dl_nbr, tb.cycle_cde"
            order_by_clause = "d.dl_nbr, tb.cycle_cde"
        
        # Use INNER JOINs for simple query as well
        from_clause = """
        FROM deal d
        INNER JOIN tranche t ON d.dl_nbr = t.dl_nbr
        INNER JOIN tranchebal tb ON t.dl_nbr = tb.dl_nbr AND t.tr_id = tb.tr_id
        """
        
        # Add calculation fields with proper aliasing
        calc_fields = []
        for calc in calculations:
            calc_name = calc['name']
            formula = calc['formula']
            # Use quoted aliases for calculation names with spaces
            calc_fields.append(f"{formula} as \"{calc_name}\"")
        
        # Assemble query
        query = f"""
        SELECT {select_clause},
            {', '.join(calc_fields)}
        {from_clause}
        {where_clause}
        GROUP BY {group_by_clause}
        ORDER BY {order_by_clause}
        """
        
        return query.strip(), params
        
    def build_calculation_subquery_tranche(self, calculation: Dict[str, Any], where_clause: str, params: Dict[str, Any]) -> str:
        """Build a subquery for a single calculation with tranche-level grouping"""
        
        calc_name = calculation['name']
        sanitized_name = self._sanitize_calc_name(calc_name)
        formula = calculation['formula']
        source_tables = calculation['source_tables']
        
        # Tranche-level grouping - always include cycle_cde
        group_by_fields = ["d.dl_nbr", "t.tr_id", "tb.cycle_cde"]
        
        # Build FROM clause with INNER JOINs
        from_clause = "FROM deal d"
        
        # Add tranche join if needed - INNER JOIN
        if any(table.startswith('tranche') for table in source_tables):
            from_clause += "\n    INNER JOIN tranche t ON d.dl_nbr = t.dl_nbr"
        
        # Add tranchebal join if needed - INNER JOIN
        if any(table.startswith('tranchebal') for table in source_tables):
            from_clause += "\n    INNER JOIN tranchebal tb ON t.dl_nbr = tb.dl_nbr AND t.tr_id = tb.tr_id"
        
        # Build the subquery
        subquery = f"""
        SELECT {', '.join(group_by_fields)},
               {formula} as {sanitized_name}
        {from_clause}
        {where_clause}
        GROUP BY {', '.join(group_by_fields)}
        ORDER BY {', '.join(group_by_fields)}
        """
        
        return subquery.strip()
    
    def preview_calculation_subquery(
        self,
        calculation: Dict[str, Any],
        aggregation_level: str = "deal",
        sample_deals: List[int] = None,
        sample_tranches: List[str] = None,
        sample_cycle: int = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL preview for a calculation with sample filters"""
        
        # Use sample data if not provided
        if not sample_deals:
            sample_deals = [101, 102, 103]
        if not sample_tranches:
            sample_tranches = ["A", "B"]
        if not sample_cycle:
            sample_cycle = 202404
        
        # Build WHERE clause with sample filters
        where_clause, params = self.filter_builder.build_where_clause(
            selected_deals=sample_deals,
            selected_tranches=sample_tranches,
            cycle_code=sample_cycle
        )
        
        # Build appropriate subquery based on aggregation level
        if aggregation_level == "tranche":
            query = self.build_calculation_subquery_tranche(calculation, where_clause, params)
        else:
            query = self.build_calculation_subquery(calculation, where_clause, params)
        
        return query, params