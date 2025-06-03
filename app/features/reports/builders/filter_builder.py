# app/features/reports/builders/filter_builder.py
"""SQL WHERE clause builder for filtering data"""

from typing import List, Dict, Any, Tuple

class FilterBuilder:
    """Builds SQL WHERE clauses for filtering report data"""
    
    def __init__(self):
        self.conditions = []
        self.parameters = {}
    
    def add_deal_filter(self, selected_deals: List[int]) -> str:
        """Add filter for selected deals"""
        if not selected_deals:
            return ""
        
        placeholders = []
        for i, deal in enumerate(selected_deals):
            param_name = f"deal_{i}"
            placeholders.append(f":{param_name}")
            self.parameters[param_name] = deal
        
        return f"d.dl_nbr IN ({', '.join(placeholders)})"
    
    def add_tranche_filter(self, selected_tranches: List[str]) -> str:
        """Add filter for selected tranches"""
        if not selected_tranches:
            return ""
        
        placeholders = []
        for i, tranche in enumerate(selected_tranches):
            param_name = f"tranche_{i}"
            placeholders.append(f":{param_name}")
            self.parameters[param_name] = tranche
        
        return f"t.tr_id IN ({', '.join(placeholders)})"
    
    def add_cycle_filter(self, cycle_code: int) -> str:
        """Add filter for cycle code"""
        if not cycle_code:
            return ""
        
        self.parameters['cycle_code'] = cycle_code
        return "tb.cycle_cde = :cycle_code"
    
    def add_custom_filters(self, filters: Dict[str, Any]) -> List[str]:
        """Add custom filters from the filters dictionary"""
        conditions = []
        
        for field, value in filters.items():
            if value is None:
                continue
            
            # Handle different filter types
            if isinstance(value, dict):
                # Range or comparison filters
                if 'min' in value and value['min'] is not None:
                    param_name = f"{field}_min"
                    conditions.append(f"{field} >= :{param_name}")
                    self.parameters[param_name] = value['min']
                
                if 'max' in value and value['max'] is not None:
                    param_name = f"{field}_max"
                    conditions.append(f"{field} <= :{param_name}")
                    self.parameters[param_name] = value['max']
                
                if 'equals' in value and value['equals'] is not None:
                    param_name = f"{field}_eq"
                    conditions.append(f"{field} = :{param_name}")
                    self.parameters[param_name] = value['equals']
            
            elif isinstance(value, list):
                # IN clause for multiple values
                if value:
                    placeholders = []
                    for i, val in enumerate(value):
                        param_name = f"{field}_{i}"
                        placeholders.append(f":{param_name}")
                        self.parameters[param_name] = val
                    conditions.append(f"{field} IN ({', '.join(placeholders)})")
            
            else:
                # Simple equality filter
                param_name = f"{field}_filter"
                conditions.append(f"{field} = :{param_name}")
                self.parameters[param_name] = value
        
        return conditions
    
    def build_where_clause(
        self, 
        selected_deals: List[int] = None,
        selected_tranches: List[str] = None,
        cycle_code: int = None,
        additional_filters: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Build complete WHERE clause with all filters"""
        
        # Reset state
        self.conditions = []
        self.parameters = {}
        
        # Add core filters
        if selected_deals:
            deal_filter = self.add_deal_filter(selected_deals)
            if deal_filter:
                self.conditions.append(deal_filter)
        
        if selected_tranches:
            tranche_filter = self.add_tranche_filter(selected_tranches)
            if tranche_filter:
                self.conditions.append(tranche_filter)
        
        if cycle_code:
            cycle_filter = self.add_cycle_filter(cycle_code)
            if cycle_filter:
                self.conditions.append(cycle_filter)
        
        # Add custom filters
        if additional_filters:
            custom_conditions = self.add_custom_filters(additional_filters)
            self.conditions.extend(custom_conditions)
        
        # Build final WHERE clause
        if self.conditions:
            where_clause = "WHERE " + " AND ".join(self.conditions)
        else:
            where_clause = ""
        
        return where_clause, self.parameters.copy()