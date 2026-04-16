import hashlib
from typing import List, Dict, Any, Optional
from models.sensitivity_model import MaskingStrategy, SensitivityRule
from services.sensitivity_service import SensitivityService

class MaskingService:
    def __init__(self, sensitivity_service: SensitivityService):
        self.sensitivity_service = sensitivity_service

    def _apply_strategy(self, value: Any, strategy: MaskingStrategy) -> Any:
        if value is None:
            return None
        
        if strategy == MaskingStrategy.NONE:
            return value
        
        if strategy == MaskingStrategy.REDACT:
            return "[REDACTED]"
        
        if strategy == MaskingStrategy.HASH:
            # Deterministic hash (using SHA-256)
            return hashlib.sha256(str(value).encode()).hexdigest()[:16]
        
        if strategy == MaskingStrategy.PARTIAL:
            # Simple partial mask for strings (e.g. email)
            s_val = str(value)
            if len(s_val) <= 4:
                return "****"
            return s_val[:2] + "****" + s_val[-2:]
            
        return value

    def mask_results(
        self, 
        results: List[Dict[str, Any]], 
        table_rules: Dict[str, List[SensitivityRule]], 
        user_role: str
    ) -> List[Dict[str, Any]]:
        """
        Transforms result rows by applying masking strategies to columns.
        """
        if not results:
            return results

        # Identify all columns and their applicable strategies
        # Note: A query might join multiple tables. 
        # For Phase 3, we'll apply masking if a column name matches any active rule in the tables involved.
        
        masked_results = []
        for row in results:
            new_row = {}
            for col, val in row.items():
                # Find the strictest masking strategy for this column across all tables
                strictest_strategy = MaskingStrategy.NONE
                
                for table, rules in table_rules.items():
                    strategy = self.sensitivity_service.resolve_masking_requirement(rules, col, user_role)
                    # Simple priority: REDACT > HASH > PARTIAL > NONE
                    priority_map = {
                        MaskingStrategy.REDACT: 3,
                        MaskingStrategy.HASH: 2,
                        MaskingStrategy.PARTIAL: 1,
                        MaskingStrategy.NONE: 0
                    }
                    if priority_map[strategy] > priority_map[strictest_strategy]:
                        strictest_strategy = strategy
                
                new_row[col] = self._apply_strategy(val, strictest_strategy)
            masked_results.append(new_row)
            
        return masked_results
