"""Add, rename, drop columns; change data types."""

from django.db import connection as django_connection
from .connection import resolve_source
from .table_ops import _validate_table_name

# PostgreSQL types we allow when changing column types
ALLOWED_PG_TYPES = {
    "TEXT", "VARCHAR", "CHAR", "INTEGER", "BIGINT", "SMALLINT",
    "DOUBLE PRECISION", "REAL", "NUMERIC", "DECIMAL",
    "BOOLEAN", "DATE", "TIMESTAMP", "TIMESTAMPTZ",
    "JSON", "JSONB", "UUID", "BYTEA",
}


def add_column(source_str, table_name, column_name, column_type, default=None, nullable=True):
    """Add a new column to a table."""
    _validate_table_name(table_name)
    _validate_table_name(column_name)
    column_type = column_type.upper().strip()
    if column_type not in ALLOWED_PG_TYPES:
        raise ValueError(f"Column type '{column_type}' is not allowed. Use one of: {', '.join(sorted(ALLOWED_PG_TYPES))}")

    src_type, src_id = resolve_source(source_str)
    conn, close = _get_conn(src_type, src_id)

    try:
        with conn.cursor() as cursor:
            null_sql = "" if nullable else " NOT NULL"
            default_sql = ""
            if default is not None:
                default_sql = f" DEFAULT '{default}'"
            cursor.execute(
                f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {column_type}{null_sql}{default_sql}'
            )
        if close:
            conn.commit()
    finally:
        if close:
            conn.close()


def rename_column(source_str, table_name, old_name, new_name):
    """Rename a column."""
    _validate_table_name(table_name)
    _validate_table_name(old_name)
    _validate_table_name(new_name)

    src_type, src_id = resolve_source(source_str)
    conn, close = _get_conn(src_type, src_id)

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f'ALTER TABLE "{table_name}" RENAME COLUMN "{old_name}" TO "{new_name}"'
            )
        if close:
            conn.commit()
    finally:
        if close:
            conn.close()


def change_column_type(source_str, table_name, column_name, new_type):
    """Change a column's data type."""
    _validate_table_name(table_name)
    _validate_table_name(column_name)
    new_type = new_type.upper().strip()
    if new_type not in ALLOWED_PG_TYPES:
        raise ValueError(f"Column type '{new_type}' is not allowed.")

    src_type, src_id = resolve_source(source_str)
    conn, close = _get_conn(src_type, src_id)

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" TYPE {new_type}'
            )
        if close:
            conn.commit()
    finally:
        if close:
            conn.close()


def drop_column(source_str, table_name, column_name):
    """Drop a column from a table."""
    _validate_table_name(table_name)
    _validate_table_name(column_name)

    src_type, src_id = resolve_source(source_str)
    conn, close = _get_conn(src_type, src_id)

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f'ALTER TABLE "{table_name}" DROP COLUMN "{column_name}"'
            )
        if close:
            conn.commit()
    finally:
        if close:
            conn.close()


def _get_conn(src_type, src_id):
    if src_type == "local":
        return django_connection, False
    from apps.db_manager.models import ExternalDatabase
    import psycopg2
    ext_db = ExternalDatabase.objects.get(pk=src_id, is_active=True)
    return psycopg2.connect(**ext_db.get_connection_params()), True
