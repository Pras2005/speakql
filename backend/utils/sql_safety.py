import sqlglot
from sqlglot import exp, parse_one
from typing import Optional, List, Set


def validate_sql_safety(sql: str, dialect: str = "postgres") -> Optional[str]:
    """
    Validates SQL safety using AST parsing via sqlglot.
    Blocks multi-statements, non-read-only operations, and dangerous DDL.
    """
    normalized_sql = sql.strip()
    if not normalized_sql:
        return "SQL query is empty"

    try:
        # sqlglot.transpile(sql, read=dialect) could also be used to check syntax
        expressions = sqlglot.parse(normalized_sql, read=dialect)
        if len(expressions) > 1:
            return "Only single-statement SQL queries are allowed"
        
        expression = expressions[0]
        if not expression:
            return "Invalid SQL statement"

        # Check for non-read-only top-level operations
        # Allowed: Select, Show, Describe, With
        allowed_types = (exp.Select, exp.Show, exp.Describe, exp.With)
        if not isinstance(expression, allowed_types):
            # If it's a Command, check if it starts with EXPLAIN
            if isinstance(expression, exp.Command) and expression.this.upper() == "EXPLAIN":
                 pass # Allow EXPLAIN commands for now
            else:
                 return f"Operation type '{type(expression).__name__}' is not allowed. Only read-only queries are permitted."

        # Recursively check for dangerous sub-expressions (e.g., in subqueries or CTEs)
        # Even if the top-level is Select, we want to block things like SELECT ... FROM (UPDATE ...)
        # although most SQL dialects don't allow this, some might have extensions.
        dangerous_types = (
            exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, 
            exp.Create, exp.Grant, exp.Revoke
        )
        for node in expression.find_all(dangerous_types):
            return f"Destructive operation '{type(node).__name__}' detected and blocked."

    except sqlglot.errors.ParseError as e:
        return f"SQL Syntax Error: {str(e)}"
    except Exception as e:
        return f"SQL Validation Error: {str(e)}"

    return None

def extract_tables(sql: str, dialect: str = "postgres") -> Set[str]:
    """
    Extracts all table names referenced in the SQL query.
    """
    tables = set()
    try:
        for expression in sqlglot.parse(sql, read=dialect):
            if not expression:
                continue
            for table in expression.find_all(exp.Table):
                # Format as schema.table if schema exists
                table_name = table.name
                if table.args.get("db"):
                    table_name = f"{table.args['db'].name}.{table_name}"
                tables.add(table_name)
    except:
        pass
    return tables
