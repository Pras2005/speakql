import os
import json
from typing import Dict, Any
from sqlalchemy import create_engine
from utils.postgres_tools import PostgreSQLTools,get_postgresql_tools
from utils.declarations import FUNCTION_DECLARATIONS
import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))


class DatabaseAgent:
    def __init__(self,user_db,debug=True,):
        """Initialize the DatabaseAgent"""
        self.debug = debug
        self.tools = get_postgresql_tools(user_db) 
        self.ai_model = self._initialize_ai()  
    
    def _initialize_ai(self):
        """Initialize the AI model"""
        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            return genai.GenerativeModel('gemini-1.5-pro')  # or whatever model you're using
        except Exception as e:
            print(f"AI initialization failed: {e}")
            raise

    
    def _clean_sql(self, sql: str) -> str:
        sql = sql.strip()  # Strip leading/trailing whitespaces
    # Remove any starting/ending '''sql or ```sql
        if sql.startswith("'''sql") or sql.startswith("```sql"):
            sql = sql[6:]  # Remove the '''sql or ```sql part
        if sql.endswith("'''") or sql.endswith("```"):
            sql = sql[:-3]  # Remove the closing block
        return sql.strip()  #
            

    def _handle_function_call(self, function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the requested database function"""
        try:
            if function_name == "list_schemas":
                return {"schemas": self.tools.list_schemas()}
            elif function_name == "list_tables":
                schema = parameters.get("schema", "public")
                return {"tables": self.tools.list_tables(schema=schema)}
            elif function_name == "describe_table":
                table_name = parameters.get("table_name")
                schema = parameters.get("schema", "public")
                return {"table_info": self.tools.describe_table(table_name=table_name, schema=schema)}
            elif function_name == "preview_data":
                table_name = parameters.get("table_name")
                schema = parameters.get("schema", "public")
                limit = parameters.get("limit", 5)
                return {"preview": self.tools.preview_data(table_name=table_name, schema=schema, limit=limit)}
            elif function_name == "count_table_rows":
                schema = parameters.get("schema", "public")
                return {"row_counts": self.tools.count_table_rows(schema=schema)}
            else:
                return {"error": f"Unknown function {function_name}"}
        except Exception as e:
            return {"error": str(e)}

    def _gather_database_structure(self) -> Dict[str, Any]:
        """Comprehensively gather database structure for all schemas and their tables."""
        db_structure = {
        "schemas": [],
        "tables": {}
        }

    # Get all schemas and their tables
        schema_table_map = self.tools.list_schemas_and_tables()
        db_structure["schemas"] = list(schema_table_map.keys())

        for schema, tables in schema_table_map.items():
            for table in tables:
                try:
                    table_info = self.tools.describe_table(table_name=table, schema=schema)
                    preview = self.tools.preview_data(table_name=table, schema=schema, limit=3)
                    row_count = self.tools.count_rows_in_table(table_name=table, schema=schema)

                    db_structure["tables"][f"{schema}.{table}"] = {
                        "structure": table_info,
                        "sample_data": preview,
                        "row_count": row_count
                    }
                except Exception as e:
                    db_structure["tables"][f"{schema}.{table}"] = {
                        "error": str(e)
                    }

        return db_structure
 
    def process_request(self, prompt: str) -> str:
        """Two-phase approach: first gather schema info, then generate SQL"""
        try:
            
            db_structure = self._gather_database_structure()
            
            if self.debug:
                print(f"Database structure gathered: {json.dumps(db_structure, indent=2,default=str)}")
            
            
            final_prompt = f"""Database Structure:
            {json.dumps(db_structure, indent=2, default=str)}
            
            User Request:
            {prompt}
            
            Generate the most appropriate PostgreSQL query based on the actual database structure above.
            Return ONLY the SQL code, no explanations or markdown.
            The SQL should be valid for PostgreSQL and match the exact column names and table structure shown above take row counts into consideration for insert queries.
            check first in which shcmea the table exist and then generate query."""
            
            if self.debug:
                print(f"Sending final prompt to AI...")
                
            sql_response = self.ai_model.generate_content(final_prompt)
            
            if sql_response and hasattr(sql_response, 'text'):
                return self._clean_sql(sql_response.text)
            else:
                print("No valid text response from AI")
                return None
        except Exception as e:
            print(f"Error in process_request: {e}")
            import traceback
            traceback.print_exc()
            return None

