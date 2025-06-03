# app/reporting/builders/report_query_builder.py
"""Main SQL query builder for reports with optimized LEFT JOINs"""

from typing import List, Dict, Any, Tuple
from .filter_builder import FilterBuilder

class ReportQueryBuilder:
    """Builds optimized SQL queries for report generation"""
    
    def __init__(self, filter_builder: FilterBuilder, subquery_builder=None):
        self.filter_builder = filter_builder
        self.subquery_builder = subquery_builder
    
    def build_calculation_subquery(self, calculation: Dict[str, Any], where_clause: str, params: Dict[str, Any]) -> str:
        """Build a subquery for a single calculation with early filtering"""
        
        calc_name = calculation['name']
        formula = calculation['formula']
        source_tables = calculation['source_tables']
        
        # Determine the main table for grouping
        main_table = "d"  # Default to deal table
        group_by_fields = ["d.dl_nbr"]
        
        # Check if we need tranche-level grouping
        if any('tranche' in table for table in source_tables):
            group_by_fields.append("t.tr_id")
        
        # Build FROM clause with JOINs
        from_clause = "FROM deal d"
        
        # Add tranche join if needed
        if any(table.startswith('tranche') for table in source_tables):
            from_clause += "\n    LEFT JOIN tranche t ON d.dl_nbr = t.dl_nbr"
        
        # Add tranchebal join if needed
        if any(table.startswith('tranchebal') for table in source_tables):
            from_clause += "\n    LEFT JOIN tranchebal tb ON t.dl_nbr = tb.dl_nbr AND t.tr_id = tb.tr_id"
        
        # Build the subquery
        subquery = f"""
        SELECT {', '.join(group_by_fields)},
               {formula} as calc_{calc_name}
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
        
        # Build subqueries for each calculation
        subqueries = []
        for calc in calculations:
            subquery = self.build_calculation_subquery(calc, where_clause, params)
            subqueries.append(f"({subquery}) as calc_{calc['name']}")
        
        # Determine grouping level
        if aggregation_level == "tranche":
            main_select = "d.dl_nbr, t.tr_id"
            main_from = """
            FROM deal d
            LEFT JOIN tranche t ON d.dl_nbr = t.dl_nbr
            """
            main_group_by = "d.dl_nbr, t.tr_id"
            join_condition = "d.dl_nbr = calc_{calc_name}.dl_nbr AND t.tr_id = calc_{calc_name}.tr_id"
        else:
            main_select = "d.dl_nbr"
            main_from = "FROM deal d"
            main_group_by = "d.dl_nbr"
            join_condition = "d.dl_nbr = calc_{calc_name}.dl_nbr"
        
        # Build main query with LEFT JOINs
        select_fields = [main_select]
        join_clauses = []
        
        for calc in calculations:
            calc_name = calc['name']
            select_fields.append(f"calc_{calc_name}.calc_{calc_name}")
            
            # Create JOIN condition for this calculation
            if aggregation_level == "tranche":
                join_condition = f"d.dl_nbr = calc_{calc_name}.dl_nbr AND t.tr_id = calc_{calc_name}.tr_id"
            else:
                join_condition = f"d.dl_nbr = calc_{calc_name}.dl_nbr"
            
            join_clauses.append(f"LEFT JOIN ({self.build_calculation_subquery(calc, where_clause, params)}) as calc_{calc_name} ON {join_condition}")
        
        # Assemble final query
        main_query = f"""
        SELECT {', '.join(select_fields)}
        {main_from}
        {chr(10).join(join_clauses)}
        {where_clause}
        GROUP BY {main_group_by}
        ORDER BY d.dl_nbr{', t.tr_id' if aggregation_level == 'tranche' else ''}
        """
        
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
        
        # Determine grouping and selection
        if aggregation_level == "tranche":
            select_clause = "d.dl_nbr, t.tr_id"
            group_by_clause = "d.dl_nbr, t.tr_id"
            order_by_clause = "d.dl_nbr, t.tr_id"
        else:
            select_clause = "d.dl_nbr"
            group_by_clause = "d.dl_nbr"
            order_by_clause = "d.dl_nbr"
        
        # Add calculation fields
        calc_fields = []
        for calc in calculations:
            calc_fields.append(f"{calc['formula']} as calc_{calc['name']}")
        
        # Build FROM clause with all necessary JOINs
        from_clause = """
        FROM deal d
        LEFT JOIN tranche t ON d.dl_nbr = t.dl_nbr
        LEFT JOIN tranchebal tb ON t.dl_nbr = tb.dl_nbr AND t.tr_id = tb.tr_id
        """
        
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