from typing import Dict, Any, Set
from utils.sql_safety import extract_tables
import re

class RiskScoringService:
    def evaluate_risk(self, sql: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluates the risk of a SQL query.
        Returns a score (0.0 to 1.0) and flags.
        """
        score = 0.1 # Baseline
        flags = []
        
        sql_upper = sql.upper()
        
        # 1. Write operations (if allowed by safety)
        write_keywords = ["INSERT", "UPDATE", "DELETE", "TRUNCATE", "DROP", "ALTER", "CREATE"]
        for kw in write_keywords:
            if kw in sql_upper:
                score += 0.5
                flags.append(f"WRITE_OPERATION_{kw}")
        
        # 2. Full table scans / SELECT *
        if "SELECT *" in sql_upper:
            score += 0.2
            flags.append("FULL_COLUMN_SCAN")
            
        if "WHERE" not in sql_upper and "SELECT" in sql_upper:
            score += 0.3
            flags.append("NO_WHERE_CLAUSE")
            
        # 3. Cross-schema queries
        tables = extract_tables(sql)
        schemas = {t.split('.')[0] for t in tables if '.' in t}
        if len(schemas) > 1:
            score += 0.2
            flags.append("CROSS_SCHEMA_QUERY")
            
        # 4. Dangerous functions (regex based as backup)
        dangerous_functions = ["pg_sleep", "current_setting", "set_config"]
        for func in dangerous_functions:
            if func in sql.lower():
                score += 0.4
                flags.append(f"DANGEROUS_FUNCTION_{func}")

        # Clamp score
        final_score = min(1.0, score)
        
        return {
            "risk_score": final_score,
            "flags": flags,
            "requires_approval": final_score >= 0.7
        }
