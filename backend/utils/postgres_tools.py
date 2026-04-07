from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import inspect, text
from typing import List, Dict, Any, Optional, Union
from time import time

from utils.db_connection import build_postgres_url
from utils.encryption import decrypt_password

SCHEMA_CACHE_TTL_SECONDS = 300
_schema_cache: Dict[str, Dict[str, Any]] = {}
_engine_cache: Dict[str, AsyncEngine] = {}

class PostgreSQLTools:
    def __init__(self, engine: AsyncEngine = None, cache_namespace: str = "default"):
        self.engine = engine
        self.cache_namespace = cache_namespace

    def set_engine(self, engine: AsyncEngine):
        """Set the database engine"""
        self.engine = engine

    def _cache_key(self, suffix: str) -> str:
        return f"{self.cache_namespace}:{suffix}"

    def _get_cached_value(self, suffix: str):
        cache_entry = _schema_cache.get(self._cache_key(suffix))
        if not cache_entry:
            return None
        if time() - cache_entry["stored_at"] > SCHEMA_CACHE_TTL_SECONDS:
            _schema_cache.pop(self._cache_key(suffix), None)
            return None
        return cache_entry["value"]

    def _set_cached_value(self, suffix: str, value: Any):
        _schema_cache[self._cache_key(suffix)] = {
            "stored_at": time(),
            "value": value,
        }

    def invalidate_cache(self):
        stale_keys = [
            cache_key for cache_key in _schema_cache
            if cache_key.startswith(f"{self.cache_namespace}:")
        ]
        for cache_key in stale_keys:
            _schema_cache.pop(cache_key, None)

    async def list_schemas(self) -> List[str]:
        """List all schemas in the database"""
        cached = self._get_cached_value("list_schemas")
        if cached is not None:
            return cached
        
        async with self.engine.connect() as conn:
            schemas = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_schema_names())
            self._set_cached_value("list_schemas", schemas)
            return schemas

    async def list_tables(self, schema: str = 'public') -> List[str]:
        """List tables in a specific schema"""
        cache_key = f"list_tables:{schema}"
        cached = self._get_cached_value(cache_key)
        if cached is not None:
            return cached
        
        async with self.engine.connect() as conn:
            tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names(schema=schema))
            self._set_cached_value(cache_key, tables)
            return tables

    async def describe_table(self, table_name: str, schema: str = 'public') -> Dict[str, Any]:
        """Get complete table metadata"""
        cache_key = f"describe_table:{schema}:{table_name}"
        cached = self._get_cached_value(cache_key)
        if cached is not None:
            return cached
            
        async with self.engine.connect() as conn:
            def get_metadata(sync_conn):
                inspector = inspect(sync_conn)
                cols = inspector.get_columns(table_name, schema=schema)
                pks = inspector.get_pk_constraint(table_name, schema=schema).get("constrained_columns", [])
                fks = inspector.get_foreign_keys(table_name, schema=schema)
                indexes = inspector.get_indexes(table_name, schema=schema)
                return cols, pks, fks, indexes

            cols, pks, fks, indexes = await conn.run_sync(get_metadata)
            
            table_info = {
                "schema": schema,
                "table_name": table_name,
                "columns": [
                    {
                        "name": c["name"],
                        "type": str(c["type"]),
                        "nullable": c["nullable"],
                        "primary_key": c["name"] in pks,
                    } for c in cols
                ],
                "foreign_keys": fks,
                "indexes": indexes
            }
            
            # Add comments (using the existing _get_column_metadata logic but async)
            for col in table_info["columns"]:
                col["comment"] = await self._get_column_comment(table_name, schema, col["name"])

            self._set_cached_value(cache_key, table_info)
            return table_info

    async def list_schemas_and_tables(self) -> Dict[str, List[str]]:
        """Return a dictionary of schemas and the tables they contain."""
        cached = self._get_cached_value("list_schemas_and_tables")
        if cached is not None:
            return cached
            
        async with self.engine.connect() as conn:
            try:
                result = await conn.execute(text("""
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
                self._set_cached_value("list_schemas_and_tables", schema_table_map)
                return schema_table_map
            except Exception as e:
                return {"error": str(e)}

    async def _get_column_comment(self, table: str, schema: str, column: str) -> Optional[str]:
        """Get column comment async"""
        async with self.engine.connect() as conn:
            try:
                result = await conn.execute(text("""
                    SELECT pgd.description FROM pg_catalog.pg_description pgd
                    JOIN pg_catalog.pg_class pgc ON pgd.objoid = pgc.oid
                    JOIN pg_catalog.pg_namespace pgn ON pgc.relnamespace = pgn.oid
                    JOIN pg_attribute pga ON pgd.objoid = pga.attrelid AND pgd.objsubid = pga.attnum
                    WHERE pgn.nspname = :schema AND pgc.relname = :table AND pga.attname = :column
                """), {'schema': schema, 'table': table, 'column': column})
                return result.scalar()
            except:
                return None

    async def count_rows_in_table(self, table_name: str, schema: str = 'public') -> int:
        """Count rows in a specific table"""
        async with self.engine.connect() as conn:
            result = await conn.execute(
                text(f'SELECT COUNT(*) FROM "{schema}"."{table_name}"')
            )
            return result.scalar()

    async def preview_data(self, table_name: str, schema: str = 'public', limit: int = 5) -> List[Dict[str, Any]]:
        """Preview table data"""
        async with self.engine.connect() as conn:
            result = await conn.execute(
                text(f'SELECT * FROM "{schema}"."{table_name}" LIMIT :limit'),
                {"limit": limit}
            )
            return [dict(row._mapping) for row in result]

    async def execute_query(self, sql: str, params: Optional[Dict] = None) -> Union[List[Dict[str, Any]], Dict[str, str]]:
        """Execute any SQL query safely"""
        async with self.engine.connect() as conn:
            try:
                result = await conn.execute(text(sql), params or {})
                if not result.returns_rows:
                    await conn.commit()
                    self.invalidate_cache()
                if result.returns_rows:
                    return [dict(row._mapping) for row in result]
                return {"status": "success", "rows_affected": result.rowcount}
            except Exception as e:
                return {"error": str(e)}

def get_postgresql_tools(user_db):
    db_password = decrypt_password(user_db.db_password_encrypted)
    url = build_postgres_url(
        host=user_db.host,
        port=user_db.port,
        db_user=user_db.db_user,
        db_password=db_password,
        db_name=user_db.db_name,
    )
    
    # Switch to async driver for the tools
    async_url = url.replace("postgresql://", "postgresql+asyncpg://")
    
    if async_url not in _engine_cache:
        _engine_cache[async_url] = create_async_engine(async_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
        
    engine = _engine_cache[async_url]
    return PostgreSQLTools(engine, cache_namespace=async_url)
