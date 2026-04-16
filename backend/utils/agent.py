import json
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

import google.generativeai as genai
from openai import OpenAI

from utils.declarations import FUNCTION_DECLARATIONS
from utils.postgres_tools import get_postgresql_tools
from core.config import settings

class LLMProvider(ABC):
    @abstractmethod
    async def generate_content(self, prompt: str) -> str:
        pass

class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(model_name)

    async def generate_content(self, prompt: str) -> str:
        response = await self.model.generate_content_async(prompt)
        return response.text

class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, model_name: str, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.client = OpenAI(
            base_url=base_url or settings.LOCAL_AI_BASE_URL,
            api_key=api_key or settings.LOCAL_AI_API_KEY
        )
        self.model_name = model_name

    async def generate_content(self, prompt: str) -> str:
        import asyncio
        def sync_call():
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        return await asyncio.to_thread(sync_call)

class DatabaseAgent:
    def __init__(self, user_db, ai_provider: LLMProvider, debug=True, semantic_context: Optional[str] = None):
        """Initialize the DatabaseAgent."""
        self.debug = debug
        self.tools = get_postgresql_tools(user_db)
        self.ai_provider = ai_provider
        self.max_steps = 6
        self.semantic_context = semantic_context or ""

    def _clean_sql(self, sql: str) -> str:
        sql = sql.strip()
        if "```sql" in sql:
             sql = sql.split("```sql")[-1].split("```")[0]
        elif "```" in sql:
             sql = sql.split("```")[-1].split("```")[0]
             
        return sql.strip().rstrip(";") + ";"

    async def _handle_function_call(self, function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a database inspection function."""
        try:
            if function_name == "list_schemas":
                return {"schemas": await self.tools.list_schemas()}
            if function_name == "list_tables":
                schema = parameters.get("schema", "public")
                return {"tables": await self.tools.list_tables(schema=schema)}
            if function_name == "describe_table":
                table_name = parameters.get("table_name")
                schema = parameters.get("schema", "public")
                if not table_name:
                    return {"error": "table_name is required"}
                return {"table_info": await self.tools.describe_table(table_name=table_name, schema=schema)}
            if function_name == "preview_data":
                table_name = parameters.get("table_name")
                schema = parameters.get("schema", "public")
                limit = parameters.get("limit", 5)
                if not table_name:
                    return {"error": "table_name is required"}
                return {"preview": await self.tools.preview_data(table_name=table_name, schema=schema, limit=limit)}
            if function_name == "count_table_rows":
                table_name = parameters.get("table_name")
                schema = parameters.get("schema", "public")
                if not table_name:
                    return {"error": "table_name is required"}
                return {"row_count": await self.tools.count_rows_in_table(table_name=table_name, schema=schema)}
            return {"error": f"Unknown function {function_name}"}
        except Exception as e:
            return {"error": str(e)}

    def _extract_json_payload(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract the first valid JSON object from model text output."""
        text = response_text.strip()
        candidates = [text]

        if "```json" in text:
            start = text.find("```json") + len("```json")
            end = text.find("```", start)
            if end != -1:
                candidates.append(text[start:end].strip())

        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            candidates.append(text[first_brace:last_brace + 1])

        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        return None

    def _tool_instructions(self) -> str:
        return json.dumps(FUNCTION_DECLARATIONS, indent=2)

    async def _build_react_prompt(self, user_prompt: str, steps: List[Dict[str, Any]]) -> str:
        scratchpad = json.dumps(steps, indent=2, default=str)
        
        try:
            full_schema = await self.tools.list_schemas_and_tables()
            total_tables = sum(len(tables) for tables in full_schema.values())
            
            if total_tables > 100:
                keywords = set(user_prompt.lower().split())
                filtered_schema = {}
                for schema, tables in full_schema.items():
                    relevant_tables = [
                        t for t in tables 
                        if any(kw in t.lower() for kw in keywords) or "public" in schema.lower()
                    ]
                    if relevant_tables:
                        filtered_schema[schema] = relevant_tables[:20]
                
                schema_summary_text = json.dumps(filtered_schema, indent=2)
                schema_summary_text += f"\n\nNOTE: Database is large ({total_tables} tables). Only showing potentially relevant tables."
            else:
                schema_summary_text = json.dumps(full_schema, indent=2)
                
        except Exception:
            schema_summary_text = "Unavailable"

        return f"""You are a PostgreSQL ReAct agent.

Available tables:
{schema_summary_text}

Semantic Knowledge (Glossary & Metrics):
{self.semantic_context}

Available tools:
{self._tool_instructions()}

Rules:
- Think step by step, but return only one JSON object.
- When you are ready, respond with a final SQL query AND a brief explanation of why you wrote it.
- Output must be valid JSON and match exactly one of these shapes:

{{
  "thought": "short reasoning",
  "action": "list_schemas|list_tables|describe_table|preview_data|count_table_rows",
  "action_input": {{}}
}}

or

{{
  "thought": "short reasoning",
  "final_sql": "SELECT ...",
  "explanation": "Brief natural language explanation of the SQL"
}}

User request:
{user_prompt}

Previous steps:
{scratchpad}
"""

    async def _run_reasoning_step(self, user_prompt: str, steps: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        react_prompt = await self._build_react_prompt(user_prompt, steps)
        if self.debug:
            print(f"Running ReAct step {len(steps) + 1}")
        response_text = await self.ai_provider.generate_content(react_prompt)
        return self._extract_json_payload(response_text)

    async def process_request(self, prompt: str) -> Dict[str, Any]:
        """Iteratively inspect the database and then generate SQL with explanation."""
        steps: List[Dict[str, Any]] = []

        try:
            for _ in range(self.max_steps):
                payload = await self._run_reasoning_step(prompt, steps)
                if not payload:
                    continue

                if payload.get("final_sql"):
                    return {
                        "sql": self._clean_sql(payload["final_sql"]),
                        "explanation": payload.get("explanation") or payload.get("thought", "Generated based on schema matching.")
                    }

                action = payload.get("action")
                action_input = payload.get("action_input") or {}
                observation = await self._handle_function_call(action, action_input)
                steps.append({
                    "thought": payload.get("thought", ""),
                    "action": action,
                    "action_input": action_input,
                    "observation": observation,
                })

            # If we reached max_steps, try one final direct call
            final_prompt = f"""User request: {prompt}
Reasoning trace: {json.dumps(steps, indent=2, default=str)}

Return a JSON object: {{"final_sql": "...", "explanation": "..."}}"""
            response_text = await self.ai_provider.generate_content(final_prompt)
            payload = self._extract_json_payload(response_text)
            if payload and payload.get("final_sql"):
                return {
                    "sql": self._clean_sql(payload["final_sql"]),
                    "explanation": payload.get("explanation") or "Final attempt generation."
                }

            return None
        except Exception as e:
            if self.debug:
                import traceback
                traceback.print_exc()
            return None
