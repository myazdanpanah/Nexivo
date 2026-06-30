"""Execute raw SQL with safety checks — admin/CEO only."""

import re
import sqlparse
from django.db import connection as django_connection
from .connection import resolve_source

# Statements that are ALLOWED (read + DML)
ALLOWED_STATEMENTS = {"SELECT", "INSERT", "UPDATE", "DELETE", "WITH", "EXPLAIN"}

# Statements that are BLOCKED (DDL / dangerous)
BLOCKED_STATEMENTS = {"DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE", "REINDEX", "COMMENT"}

QUERY_TIMEOUT_SECONDS = 30


def execute_sql(source_str, sql, allow_multi=False):
    """
    Execute a SQL query with safety guardrails.

    Args:
        source_str: "local" or "external_<id>".
        sql: The SQL string.
        allow_multi: If True, allow multiple statements (admin override).

    Returns:
        For SELECT: {columns, data, row_count}
        For DML: {rows_affected}
        For blocked: raises ValueError
    """
    sql = sql.strip().rstrip(";").strip()
    if not sql:
        raise ValueError("Empty SQL query")

    # Parse with sqlparse to extract individual statements
    parsed = sqlparse.parse(sql)
    statements = [str(s).strip() for s in parsed if str(s).strip()]

    if len(statements) > 1 and not allow_multi:
        raise ValueError(
            "Multiple statements not allowed. Enable multi-statement mode or execute one query at a time."
        )

    # Safety check on each statement
    for stmt in statements:
        first_word = _get_first_keyword(stmt).upper()
        if first_word in BLOCKED_STATEMENTS:
            raise ValueError(f"Statement '{first_word}' is not allowed for security reasons.")
        if first_word not in ALLOWED_STATEMENTS:
            raise ValueError(f"Statement '{first_word}' is not allowed.")

    src_type, src_id = resolve_source(source_str)
    conn, close = _get_conn(src_type, src_id)

    try:
        with conn.cursor() as cursor:
            # Execute the last statement (or only statement)
            last_stmt = statements[-1].strip()
            cursor.execute(last_stmt)

            first_word = _get_first_keyword(last_stmt).upper()

            if first_word in ("SELECT", "WITH", "EXPLAIN"):
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return {
                    "columns": columns,
                    "data": rows,
                    "row_count": len(rows),
                }
            else:
                return {"rows_affected": cursor.rowcount}
    finally:
        if close:
            conn.close()


def _get_first_keyword(sql):
    """Extract the first keyword from a SQL statement."""
    tokens = sqlparse.parse(sql)[0].tokens
    for token in tokens:
        if token.ttype in (sqlparse.tokens.Keyword, sqlparse.tokens.Keyword.DDL, sqlparse.tokens.Keyword.DML):
            return str(token).strip()
    # Fallback: first word
    return sql.split()[0] if sql.split() else ""


def _get_conn(src_type, src_id):
    if src_type == "local":
        return django_connection, False
    from apps.db_manager.models import ExternalDatabase
    import psycopg2
    ext_db = ExternalDatabase.objects.get(pk=src_id, is_active=True)
    return psycopg2.connect(**ext_db.get_connection_params()), True
