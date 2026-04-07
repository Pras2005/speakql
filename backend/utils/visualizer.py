import json

async def format_db_structure_for_visualization(db_agent):
    """
    Formats the database structure into a JSON format suitable for the visualization component.
    """
    result = {
        "schemas": [],
        "tables": {}
    }

    # Get schemas
    try:
        result["schemas"] = await db_agent.tools.list_schemas()
    except Exception as e:
        result["schemas"] = []

    # Focus on public schema for now
    schema = "public"

    try:
        tables = await db_agent.tools.list_tables(schema=schema)

        for table_name in tables:
            try:
                # Get table structure
                table_info = await db_agent.tools.describe_table(table_name=table_name, schema=schema)

                # Get sample data
                sample_data = await db_agent.tools.preview_data(table_name=table_name, schema=schema, limit=3)

                processed_sample = []
                for row in sample_data:
                    processed_row = {}
                    for key, value in row.items():
                        processed_row[key] = str(value) if value is not None else None
                    processed_sample.append(processed_row)

                result["tables"][table_name] = {
                    "structure": table_info,
                    "sample_data": processed_sample
                }

            except Exception as e:
                result["tables"][table_name] = {"error": str(e)}

    except Exception as e:
        pass

    return result


async def get_db_structure_json(db_agent):
    """
    Converts the database structure into a pretty-printed JSON string.
    """
    db_structure = await format_db_structure_for_visualization(db_agent)
    return json.dumps(db_structure, indent=2)
