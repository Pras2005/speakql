from sqlalchemy.engine import Engine
from sqlalchemy import inspect, text
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet
from models.db_model import UserDatabase
from utils.encryption import decrypt_password
from sqlalchemy import create_engine

class PostgreSQLTools:
    def __init__(self, engine: Engine = None):
        self.engine = engine

    def set_engine(self, engine: Engine):
        """Set the database engine"""
        self.engine = engine

    def list_schemas(self) -> List[str]:
        """List all schemas in the database"""
        return inspect(self.engine).get_schema_names()

    def list_tables(self, schema: str = 'public') -> List[str]:
        """List tables in a specific schema"""
        return inspect(self.engine).get_table_names(schema=schema)

    def describe_table(self, table_name: str, schema: str = 'public') -> Dict[str, Any]:
        """Get complete table metadata"""
        inspector = inspect(self.engine)
        cols = inspector.get_columns(table_name, schema=schema)
        pks = inspector.get_pk_constraint(table_name, schema=schema).get("constrained_columns", [])
        fks = inspector.get_foreign_keys(table_name, schema=schema)
        indexes = inspector.get_indexes(table_name, schema=schema)
        
        return {
            "schema": schema,
            "table_name": table_name,
            "columns": [
                {
                    "name": c["name"],
                    "type": str(c["type"]),
                    "nullable": c["nullable"],
                    "primary_key": c["name"] in pks,
                    **self._get_column_metadata(table_name, schema, c["name"])
                } for c in cols
            ],
            "foreign_keys": fks,
            "indexes": indexes
        }
    def list_schemas_and_tables(self) -> Dict[str, List[str]]:
        """Return a dictionary of schemas and the tables they contain."""
        with self.engine.connect() as conn:
            try:
                result = conn.execute(text("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
                ORDER BY table_schema, table_name;
                """))
                schema_table_map = {}
                for row in result:
                    schema = row._mapping["table_schema"]
                    table = row._mapping["table_name"]
                    if schema not in schema_table_map:
                        schema_table_map[schema] = []
                    schema_table_map[schema].append(table)
                return schema_table_map
            except Exception as e:
                print({"error": str(e)})
                return {"error": str(e)}
    def _get_column_metadata(self, table: str, schema: str, column: str) -> Dict[str, Any]:
        """Get additional column metadata like comments"""
        with self.engine.connect() as conn:
            try:
                comment = conn.execute(text("""
                    SELECT pgd.description FROM pg_catalog.pg_description pgd
                    JOIN pg_catalog.pg_class pgc ON pgd.objoid = pgc.oid
                    JOIN pg_catalog.pg_namespace pgn ON pgc.relnamespace = pgn.oid
                    JOIN pg_attribute pga ON pgd.objoid = pga.attrelid AND pgd.objsubid = pga.attnum
                    WHERE pgn.nspname = :schema AND pgc.relname = :table AND pga.attname = :column
                """), {'schema': schema, 'table': table, 'column': column}).scalar()
                return {"comment": comment}
            except:
                return {}
    def count_rows_in_table(self, table_name: str, schema: str = 'public') -> int:
        """Count rows in a specific table"""
        with self.engine.connect() as conn:
            result = conn.execute(
                text(f'SELECT COUNT(*) FROM "{schema}"."{table_name}"')
            )
            return result.scalar()

    def preview_data(self, table_name: str, schema: str = 'public', limit: int = 5) -> List[Dict[str, Any]]:
        """Preview table data"""
        with self.engine.connect() as conn:
            result = conn.execute(
                text(f'SELECT * FROM "{schema}"."{table_name}" LIMIT :limit'),
                {"limit": limit}
            )
            return [dict(row._mapping) for row in result]

    def execute_query(self, sql: str, params: Optional[Dict] = None) -> Union[List[Dict[str, Any]], Dict[str, str]]:
        """Execute any SQL query safely"""
        with self.engine.connect() as conn:
            try:
                result = conn.execute(text(sql), params or {})
                if not result.returns_rows:
                    conn.commit()
                if result.returns_rows:
                    return [dict(row._mapping) for row in result]
                return {"status": "success", "rows_affected": result.rowcount}
            except Exception as e:
                print({"error":str(e)})
                return {"error": str(e)}



def get_postgresql_tools(user_db):
    db_password = decrypt_password(user_db.db_password_encrypted)
    url = f"postgresql://{user_db.db_user}:{db_password}@{user_db.host}:{user_db.port}/{user_db.db_name}"
    engine = create_engine(url)
    return PostgreSQLTools(engine)

