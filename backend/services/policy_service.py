from repositories.policy_repository import PolicyRepository
from models.policy_model import Policy
from typing import List, Optional, Dict, Any, Set
from utils.sql_safety import extract_tables
import logging
import sqlglot
from sqlglot import exp

logger = logging.getLogger(__name__)

# Mapping of keyword string to AST node types for robust DDL detection
_KEYWORD_TO_AST = {
    "DROP": exp.Drop,
    "ALTER": exp.Alter,
    "TRUNCATE": exp.Truncate,
    "CREATE": exp.Create,
    "INSERT": exp.Insert,
    "UPDATE": exp.Update,
    "DELETE": exp.Delete,
    "GRANT": exp.Grant,
    "REVOKE": exp.Revoke,
}


def _sql_contains_keyword(sql: str, keyword: str) -> bool:
    """
    Checks whether a SQL statement semantically contains a given keyword operation.
    For known DDL/DML keywords we use AST node detection to avoid false positives from
    comments, string literals, or table names. Unknown keywords fall back to case-insensitive
    substring search.
    """
    kw_upper = keyword.upper()
    ast_type = _KEYWORD_TO_AST.get(kw_upper)
    if ast_type is not None:
        try:
            expressions = sqlglot.parse(sql, read="postgres")
            if expressions and expressions[0]:
                return any(True for _ in expressions[0].find_all(ast_type))
            return False
        except Exception:
            pass  # fall through to string check
    # Fallback for custom/unknown keywords
    return kw_upper in sql.upper()


class PolicyService:
    def __init__(self, policy_repo: PolicyRepository):
        self.policy_repo = policy_repo

    async def get_active_policies(self, workspace_id: int) -> List[Policy]:
        return await self.policy_repo.list_by_workspace(workspace_id)

    def evaluate_policy(self, policies: List[Policy], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a set of policies against a request context.
        context keys: 'sql', 'is_write', 'tables', 'user_role', etc.
        """
        decision = {
            "allowed": True,
            "reason": "Allowed by default",
            "limit_rows": None,
            "timeout": None,
            "masking": []
        }

        sql = context.get("sql", "")
        referenced_tables = context.get("tables")
        if referenced_tables is None and sql:
            referenced_tables = extract_tables(sql)

        for policy in policies:
            rules = policy.rules_json

            # 1. Block Write Operations
            if rules.get("block_write") and context.get("is_write"):
                return {
                    "allowed": False,
                    "reason": f"Policy '{policy.name}' blocks write operations",
                    "policy_id": policy.id
                }

            # 1b. Role-based restrictions
            restricted_roles = rules.get("restricted_roles", [])
            if context.get("user_role") in restricted_roles:
                return {
                    "allowed": False,
                    "reason": f"Role '{context['user_role']}' is restricted by policy '{policy.name}'",
                    "policy_id": policy.id
                }

            # 2. Blocked Keywords — AST-aware detection
            blocked_keywords = rules.get("blocked_keywords", [])
            for kw in blocked_keywords:
                if _sql_contains_keyword(sql, kw):
                    return {
                        "allowed": False,
                        "reason": f"Policy '{policy.name}' blocks keyword: {kw}",
                        "policy_id": policy.id
                    }

            # 3. Allowed/Blocked Tables and Schemas
            if referenced_tables:
                # Table-level allowlist
                allowed_tables = rules.get("allowed_tables")
                if allowed_tables is not None:
                    for table in referenced_tables:
                        if table not in allowed_tables:
                            return {
                                "allowed": False,
                                "reason": f"Table '{table}' is not in the allowed list for policy '{policy.name}'",
                                "policy_id": policy.id
                            }
                
                # Schema-level allowlist
                allowed_schemas = rules.get("allowed_schemas")
                if allowed_schemas is not None:
                    for table in referenced_tables:
                        schema = table.split('.')[0] if '.' in table else "public"
                        if schema not in allowed_schemas:
                            return {
                                "allowed": False,
                                "reason": f"Schema '{schema}' is not in the allowed list for policy '{policy.name}'",
                                "policy_id": policy.id
                            }

                # Blocked tables
                blocked_tables = rules.get("blocked_tables", [])
                for table in referenced_tables:
                    if table in blocked_tables:
                        return {
                            "allowed": False,
                            "reason": f"Table '{table}' is blocked by policy '{policy.name}'",
                            "policy_id": policy.id
                        }

            # 4. Row limit enforcement (cumulative - take the strictest)
            row_limit = rules.get("row_limit")
            if row_limit is not None:
                if decision["limit_rows"] is None or row_limit < decision["limit_rows"]:
                    decision["limit_rows"] = row_limit
                    decision["reason"] = f"Strict row limit of {row_limit} enforced by policy '{policy.name}'"

            # 5. Execution Timeout (cumulative - take the strictest)
            timeout = rules.get("execution_timeout")
            if timeout is not None:
                if decision["timeout"] is None or timeout < decision["timeout"]:
                    decision["timeout"] = timeout

            # 6. Result Size Cap (cumulative - take the strictest)
            size_cap = rules.get("result_size_cap")
            if size_cap is not None:
                if decision.get("size_cap") is None or size_cap < decision["size_cap"]:
                    decision["size_cap"] = size_cap

        return decision
