"""List tables, get schema, browse data, count rows."""

from django.db import connection as django_connection
from .connection import resolve_source


def list_tables(source_str):
    """Return list of table names for the given source."""
    src_type, src_id = resolve_source(source_str)

    if src_type == "local":
        with django_connection.cursor() as cursor:
            cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
                "ORDER BY table_name"
            )
            return [row[0] for row in cursor.fetchall()]
    else:
        from apps.db_manager.models import ExternalDatabase
        import psycopg2

        ext_db = ExternalDatabase.objects.get(pk=src_id, is_active=True)
        conn = psycopg2.connect(**ext_db.get_connection_params())
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
                    "ORDER BY table_name"
                )
                return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()


def get_table_schema(source_str, table_name):
    """Return list of {name, type, nullable, default, max_length} for columns."""
    src_type, src_id = resolve_source(source_str)
    _validate_table_name(table_name)

    if src_type == "local":
        conn = django_connection
        close = False
    else:
        from apps.db_manager.models import ExternalDatabase
        import psycopg2
        ext_db = ExternalDatabase.objects.get(pk=src_id, is_active=True)
        conn = psycopg2.connect(**ext_db.get_connection_params())
        close = True

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT column_name, data_type, is_nullable, "
                "column_default, character_maximum_length "
                "FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = %s "
                "ORDER BY ordinal_position",
                [table_name],
            )
            cols = []
            for row in cursor.fetchall():
                cols.append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2] == "YES",
                    "default": row[3],
                    "max_length": row[4],
                })
            return cols
    finally:
        if close:
            conn.close()


def browse_data(source_str, table_name, offset=0, limit=100, order_by=None, order_dir="ASC"):
    """Return {columns, rows, total_count} for a table."""
    src_type, src_id = resolve_source(source_str)
    _validate_table_name(table_name)

    if src_type == "local":
        conn = django_connection
        close = False
    else:
        from apps.db_manager.models import ExternalDatabase
        import psycopg2
        ext_db = ExternalDatabase.objects.get(pk=src_id, is_active=True)
        conn = psycopg2.connect(**ext_db.get_connection_params())
        close = True

    try:
        with conn.cursor() as cursor:
            # Total count
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            total_count = cursor.fetchone()[0]

            # Validate order_by column
            if order_by:
                cursor.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = %s",
                    [table_name],
                )
                valid_cols = {row[0] for row in cursor.fetchall()}
                if order_by not in valid_cols:
                    order_by = None

            order_sql = ""
            if order_by:
                direction = "DESC" if order_dir.upper() == "DESC" else "ASC"
                order_sql = f' ORDER BY "{order_by}" {direction}'

            cursor.execute(
                f'SELECT * FROM "{table_name}"{order_sql} LIMIT %s OFFSET %s',
                [limit, offset],
            )
            columns = [desc[0] for desc in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return {
                "columns": columns,
                "rows": rows,
                "total_count": total_count,
                "offset": offset,
                "limit": limit,
            }
    finally:
        if close:
            conn.close()


def count_rows(source_str, table_name):
    """Return total row count for a table."""
    src_type, src_id = resolve_source(source_str)
    _validate_table_name(table_name)

    if src_type == "local":
        conn = django_connection
        close = False
    else:
        from apps.db_manager.models import ExternalDatabase
        import psycopg2
        ext_db = ExternalDatabase.objects.get(pk=src_id, is_active=True)
        conn = psycopg2.connect(**ext_db.get_connection_params())
        close = True

    try:
        with conn.cursor() as cursor:
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            return cursor.fetchone()[0]
    finally:
        if close:
            conn.close()


def _validate_table_name(name):
    """Basic protection against SQL injection in table names."""
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', name):
        raise ValueError(f"Invalid table name: {name}")
