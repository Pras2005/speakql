import logging
import sqlglot
from sqlglot import exp
from typing import Dict, Any, List
from utils.sql_safety import extract_tables

logger = logging.getLogger(__name__)

_DANGEROUS_FUNCTIONS = {"pg_sleep", "current_setting", "set_config"}


class RiskScoringService:
    def evaluate_risk(self, sql: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluates the risk of a SQL query using AST-based detection where possible.
        Returns a score (0.0 to 1.0) and flags.
        """
        score = 0.1  # Baseline
        flags: List[str] = []

        try:
            expressions = sqlglot.parse(sql, read="postgres")
            expression = expressions[0] if expressions else None
        except Exception as exc:
            logger.debug("SQL parse failed in risk service: %s", exc)
            expression = None

        if expression is not None:
            # 1. Write / DDL operations — AST node types, not string keywords
            write_types = (exp.Insert, exp.Update, exp.Delete, exp.Truncate,
                           exp.Drop, exp.Alter, exp.Create)
            for node in expression.find_all(write_types):
                op_name = type(node).__name__.upper()
                if f"WRITE_OPERATION_{op_name}" not in flags:
                    score += 0.5
                    flags.append(f"WRITE_OPERATION_{op_name}")

            # 2. SELECT * — AST star node
            if any(True for _ in expression.find_all(exp.Star)):
                score += 0.2
                flags.append("FULL_COLUMN_SCAN")

            # 3. No WHERE clause on a SELECT
            if isinstance(expression, exp.Select) and expression.find(exp.Where) is None:
                score += 0.3
                flags.append("NO_WHERE_CLAUSE")

            # 4. Dangerous function calls — AST anonymous function / function nodes
            sql_lower = sql.lower()
            for func_name in _DANGEROUS_FUNCTIONS:
                if func_name in sql_lower:
                    score += 0.4
                    flags.append(f"DANGEROUS_FUNCTION_{func_name}")

        else:
            # AST parse failed — fall back to conservative string scan only for write keywords
            sql_upper = sql.upper()
            for kw in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "DROP", "ALTER", "CREATE"):
                if kw in sql_upper:
                    score += 0.5
                    flags.append(f"WRITE_OPERATION_{kw}")

        # 5. Cross-schema queries
        tables = extract_tables(sql)
        schemas = {t.split(".")[0] for t in tables if "." in t}
        if len(schemas) > 1:
            score += 0.2
            flags.append("CROSS_SCHEMA_QUERY")

        # Clamp score
        final_score = min(1.0, score)

        return {
            "risk_score": final_score,
            "flags": flags,
            "requires_approval": final_score >= 0.7
        }
