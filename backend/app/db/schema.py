from __future__ import annotations

from typing import Dict, List

from psycopg2.extras import RealDictCursor

from app.db.connection import get_connection


SCHEMA_QUERY = """
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
"""


def fetch_public_schema() -> Dict[str, List[str]]:
    schema: Dict[str, List[str]] = {}
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(SCHEMA_QUERY)
            for row in cur.fetchall():
                table_name = row["table_name"]
                schema.setdefault(table_name, []).append(row["column_name"])
    finally:
        conn.close()
    return schema


def format_schema(schema: Dict[str, List[str]]) -> str:
    if not schema:
        return "No public tables found."
    return "\n".join([f"- {table}: {', '.join(columns)}" for table, columns in schema.items()])
