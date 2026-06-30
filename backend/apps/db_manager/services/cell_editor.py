"""Inline cell updates — single and batch."""

import json
from django.db import connection as django_connection
from .connection import resolve_source
from .table_ops import _validate_table_name


def update_cell(source_str, table_name, pk_column, pk_value, column, value):
    """Update a single cell value. Returns rows_affected."""
    src_type, src_id = resolve_source(source_str)
    _validate_table_name(table_name)
    _validate_table_name(column)
    _validate_table_name(pk_column)

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
                f'UPDATE "{table_name}" SET "{column}" = %s WHERE "{pk_column}" = %s',
                [_convert_value(value), pk_value],
            )
            return cursor.rowcount
    finally:
        if close:
            conn.close()


def batch_update(source_str, table_name, updates):
    """
    Batch update multiple cells.
    updates: list of {pk_column, pk_value, column, value}
    Returns total rows_affected.
    """
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

    total = 0
    try:
        with conn.cursor() as cursor:
            for upd in updates:
                _validate_table_name(upd["pk_column"])
                _validate_table_name(upd["column"])
                cursor.execute(
                    f'UPDATE "{table_name}" SET "{upd["column"]}" = %s '
                    f'WHERE "{upd["pk_column"]}" = %s',
                    [_convert_value(upd["value"]), upd["pk_value"]],
                )
                total += cursor.rowcount
        if close:
            conn.commit()
        return total
    finally:
        if close:
            conn.close()


def insert_row(source_str, table_name, data):
    """Insert a new row. data: dict of {column: value}. Returns inserted row."""
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
            cols = list(data.keys())
            for c in cols:
                _validate_table_name(c)
            placeholders = ", ".join(["%s"] * len(cols))
            col_names = ", ".join([f'"{c}"' for c in cols])
            values = [_convert_value(data[c]) for c in cols]
            cursor.execute(
                f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders}) RETURNING *',
                values,
            )
            row = cursor.fetchone()
            col_desc = [desc[0] for desc in cursor.description]
            result = dict(zip(col_desc, row)) if row else None
        if close:
            conn.commit()
        return result
    finally:
        if close:
            conn.close()


def delete_rows(source_str, table_name, pk_column, pk_values):
    """Delete rows by primary key values. Returns rows_affected."""
    src_type, src_id = resolve_source(source_str)
    _validate_table_name(table_name)
    _validate_table_name(pk_column)

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
            placeholders = ", ".join(["%s"] * len(pk_values))
            cursor.execute(
                f'DELETE FROM "{table_name}" WHERE "{pk_column}" IN ({placeholders})',
                pk_values,
            )
            return cursor.rowcount
    finally:
        if close:
            conn.commit()
            conn.close()


def _convert_value(value):
    """Convert a Python value to a PostgreSQL-compatible value."""
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return value
