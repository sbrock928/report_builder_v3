# app/features/reports/builders/subquery_builder.py
from typing import Dict, Any

class SubqueryBuilder:
    """Builds filtered subqueries for individual calculations using actual DW models"""
    
    def __init__(self, base_where_clause: str, base_params: Dict[str, Any]):
        self.base_where_clause = base_where_clause
        self.base_params = base_params
    
    def build_calculation_subquery(
        self, 
        calc_config: Dict[str, Any],
        aggregation_level: str,
        alias: str
    ) -> str:
        """
        Build a subquery for a single calculation with early filtering applied
        """
        # Determine grouping based on aggregation level
        if aggregation_level == "deal":
            group_by = "d.dl_nbr"
            select_fields = "d.dl_nbr"
        else:  # tranche level
            group_by = "d.dl_nbr, t.tr_id"
            select_fields = "d.dl_nbr, t.tr_id"
        
        # Build the JOIN clauses for source tables
        joins = self._build_joins(calc_config['source_tables'])
        
        subquery = f"""
        (
            SELECT 
                {select_fields},
                {calc_config['formula']} as {alias}
            FROM deal d
            {joins}
            WHERE {self.base_where_clause}
            GROUP BY {group_by}
        ) {alias}
        """
        
        return subquery.strip()
    
    def _build_joins(self, source_tables: list) -> str:
        """Build necessary JOIN clauses based on source tables using actual DW models"""
        joins = []
        has_tranche = False
        has_tranchebal = False
        
        for table_alias in source_tables:
            table_name = table_alias.split(' ')[0]  # Extract table name from "table alias" format
            
            if table_name == "tranche":
                has_tranche = True
            elif table_name == "tranchebal":
                has_tranchebal = True
        
        # Always join tranche if we need tranchebal or if tranche is explicitly requested
        if has_tranche or has_tranchebal:
            joins.append("LEFT JOIN tranche t ON d.dl_nbr = t.dl_nbr")
        
        # Join tranchebal if needed
        if has_tranchebal:
            joins.append("LEFT JOIN tranchebal tb ON t.dl_nbr = tb.dl_nbr AND t.tr_id = tb.tr_id")
        
        return "\n            ".join(joins)