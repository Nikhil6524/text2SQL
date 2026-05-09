from __future__ import annotations

from typing import Any, Dict, List

from fastapi import HTTPException
from psycopg2.extras import RealDictCursor

from app.db.connection import get_connection
from app.db.schema import fetch_public_schema, format_schema
from app.db.sql_guard import should_block_user_request, validate_sql
from app.models.schemas import ChatMessage
from app.services.groq_client import groq_client


SYSTEM_PROMPT_TEMPLATE = """
You are a database assistant that converts user requests into SAFE SQL actions.

Allowed operations only:
- SELECT (including aggregates like COUNT, AVG, MIN, MAX, SUM, GROUP BY)
- INSERT
- UPDATE

Never generate SQL for DELETE or schema changes (DROP/ALTER/TRUNCATE/CREATE/REPLACE/etc).
If user asks forbidden operations, return an action "deny".

You MUST return valid JSON with this shape:
{{
    "action": "select" | "insert" | "update" | "deny",
    "sql": "string (empty for deny)",
    "params": {{"key": "value"}},
    "assistant_message": "short natural response"
}}

Rules:
- Use only tables and columns from this schema:
{schema_text}
- Use named parameters in psycopg2 format, e.g. %(name)s
- Keep a single SQL statement only.
- For UPDATE, include a WHERE clause.
- If request is ambiguous, choose deny with a helpful message.
- If user asks for statistics, use a SELECT with aggregates.
""".strip()


class ChatService:
    @staticmethod
    def _execute_sql(sql: str, params: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                if sql.upper().startswith("SELECT"):
                    rows = cur.fetchall()
                    return {"data": rows, "rows_affected": len(rows)}

                conn.commit()
                return {"data": None, "rows_affected": cur.rowcount}
        except Exception as exc:
            conn.rollback()
            raise HTTPException(status_code=400, detail=f"SQL execution error: {exc}") from exc
        finally:
            conn.close()

    def process(self, message: str, history: List[ChatMessage]) -> Dict[str, Any]:
        if should_block_user_request(message):
            return {
                "reply": "I can help with reading, adding, and updating data. I cannot delete data or change database structure.",
                "action": "deny",
                "blocked": True,
                "sql_executed": None,
                "data": None,
                "rows_affected": None,
            }

        schema = fetch_public_schema()
        if not schema:
            raise HTTPException(status_code=400, detail="No public tables found in connected PostgreSQL database")

        recent_history = history[-8:]
        history_block = "\n".join([f"{h.role}: {h.content}" for h in recent_history])

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(schema_text=format_schema(schema))
        user_prompt = f"""
Conversation history:
{history_block if history_block else 'No prior history'}

User request:
{message}
""".strip()

        plan = groq_client.plan_sql(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

        action = str(plan.get("action", "deny")).strip().lower()
        assistant_message = str(plan.get("assistant_message", "I processed your request.")).strip()

        if action == "deny":
            return {
                "reply": assistant_message,
                "action": "deny",
                "blocked": True,
                "sql_executed": None,
                "data": None,
                "rows_affected": None,
            }

        params = plan.get("params", {})
        if not isinstance(params, dict):
            params = {}

        safe_sql = validate_sql(str(plan.get("sql", "")), schema)
        result = self._execute_sql(safe_sql, params)

        if action == "select":
            row_count = int(result["rows_affected"] or 0)
            if row_count == 0:
                reply = "I checked the database and found no matching records."
            else:
                reply = f"I found {row_count} record(s). {assistant_message}"
        else:
            affected = int(result["rows_affected"] or 0)
            reply = f"Done. {affected} row(s) affected. {assistant_message}"

        return {
            "reply": reply,
            "action": action,
            "blocked": False,
            "sql_executed": safe_sql,
            "data": result["data"],
            "rows_affected": result["rows_affected"],
        }


chat_service = ChatService()
