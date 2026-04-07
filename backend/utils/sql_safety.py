import re
from typing import Optional


READ_ONLY_PATTERN = re.compile(r"^\s*(select|with|show|explain)\b", re.IGNORECASE)
DANGEROUS_PATTERN = re.compile(
    r"\b(insert|update|delete|alter|drop|truncate|create|grant|revoke|copy|call|do)\b",
    re.IGNORECASE,
)


def validate_sql_safety(sql: str) -> Optional[str]:
    normalized_sql = sql.strip()
    if not normalized_sql:
        return "SQL query is empty"

    statements = [segment.strip() for segment in normalized_sql.split(";") if segment.strip()]
    if len(statements) != 1:
        return "Only single-statement SQL queries are allowed"

    if not READ_ONLY_PATTERN.match(normalized_sql):
        if DANGEROUS_PATTERN.search(normalized_sql):
            return "Only read-only SQL is allowed from the agent execution endpoint"
        return "Query must start with SELECT, WITH, SHOW, or EXPLAIN"

    return None
