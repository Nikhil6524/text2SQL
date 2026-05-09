from __future__ import annotations

import re
from typing import Dict, List

from fastapi import HTTPException


FORBIDDEN_SQL_WORDS = {
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "REPLACE",
    "GRANT",
    "REVOKE",
    "VACUUM",
    "CALL",
    "EXEC",
    "MERGE",
}


def should_block_user_request(message: str) -> bool:
    blocked_patterns = [
        r"\bdelete\b",
        r"\bdrop\b",
        r"\balter\b",
        r"\btruncate\b",
        r"\bchange\s+table\b",
        r"\bremove\s+column\b",
        r"\bmodify\s+schema\b",
    ]
    text = message.lower()
    return any(re.search(pattern, text) for pattern in blocked_patterns)


def _normalize_identifier(identifier: str) -> str:
    if "." in identifier:
        identifier = identifier.split(".", 1)[1]
    return identifier.strip().strip('"')


def _extract_tables(sql: str) -> list[str]:
    patterns = [
        r"\bFROM\s+([a-zA-Z_][\w\.]*)",
        r"\bJOIN\s+([a-zA-Z_][\w\.]*)",
        r"\bINTO\s+([a-zA-Z_][\w\.]*)",
        r"\bUPDATE\s+([a-zA-Z_][\w\.]*)",
    ]

    tables: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, sql, flags=re.IGNORECASE):
            tables.append(_normalize_identifier(match))
    return list(set(tables))


def validate_sql(sql: str, schema: Dict[str, List[str]]) -> str:
    cleaned = sql.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Generated SQL is empty")

    if ";" in cleaned[:-1]:
        raise HTTPException(status_code=400, detail="Only one SQL statement is allowed")

    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    first_word_match = re.match(r"^\s*([a-zA-Z]+)", cleaned)
    if not first_word_match:
        raise HTTPException(status_code=400, detail="Unable to parse SQL command")

    command = first_word_match.group(1).upper()
    if command not in {"SELECT", "INSERT", "UPDATE"}:
        raise HTTPException(status_code=400, detail="Only SELECT, INSERT, UPDATE are allowed")

    upper_sql = cleaned.upper()
    for forbidden in FORBIDDEN_SQL_WORDS:
        if re.search(rf"\b{forbidden}\b", upper_sql):
            raise HTTPException(status_code=400, detail=f"SQL contains forbidden operation: {forbidden}")

    if command == "UPDATE" and " WHERE " not in f" {upper_sql} ":
        raise HTTPException(status_code=400, detail="UPDATE must include a WHERE clause")

    allowed_tables = set(schema.keys())
    for table in _extract_tables(cleaned):
        if table not in allowed_tables:
            raise HTTPException(status_code=400, detail=f"Unknown or unauthorized table: {table}")

    return cleaned
