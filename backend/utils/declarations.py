from typing import Dict, Any

FUNCTION_DECLARATIONS = [
    {
        "name": "list_schemas",
        "description": "List all available schemas in the database",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "list_tables",
        "description": "List tables in a specific schema",
        "parameters": {
            "type": "object",
            "properties": {
                "schema": {
                    "type": "string",
                    "description": "Schema name (default: public)",
                    "default": "public"
                }
            },
            "required": []
        }
    },
    {
        "name": "describe_table",
        "description": "Get complete structure of a table including columns, constraints, and indexes",
        "parameters": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table to describe"
                },
                "schema": {
                    "type": "string",
                    "description": "Schema name (default: public)",
                    "default": "public"
                }
            },
            "required": ["table_name"]
        }
    },
    {
        "name": "preview_data",
        "description": "Preview sample data from a table",
        "parameters": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table"
                },
                "schema": {
                    "type": "string",
                    "description": "Schema name (default: public)",
                    "default": "public"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of rows to return (default: 5)",
                    "default": 5
                }
            },
            "required": ["table_name"]
        }
    },
    {
        "name": "count_table_rows",
        "description": "Count rows in a specific table",
        "parameters": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table"
                },
                "schema": {
                    "type": "string",
                    "description": "Schema name (default: public)",
                    "default": "public"
                }
            },
            "required": ["table_name"]
        }
    }
]
