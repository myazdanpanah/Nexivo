"""Import XLSX, XLS, CSV with replace/append/upsert modes."""

import os
import tempfile
import re
import pandas as pd
from django.db import connection as django_connection, transaction
from .connection import resolve_source
from .table_ops import _validate_table_name

PG_TYPE_MAP = {
    "int64": "BIGINT",
    "float64": "DOUBLE PRECISION",
    "object": "TEXT",
    "bool": "BOOLEAN",
    "datetime64[ns]": "TIMESTAMP",
}


def import_file(file, source_str, table_name, mode="replace", key_column=None):
    """
    Import an uploaded file into a PostgreSQL table.

    Args:
        file: Django InMemoryUploadedFile or similar file-like object.
        source_str: "local" or "external_<id>".
        table_name: Target table name.
        mode: "replace", "append", or "upsert".
        key_column: For upsert mode, the column to match on.

    Returns:
        dict with rows_affected, warnings.
    """
    _validate_table_name(table_name)

    # Save file temporarily
    suffix = os.path.splitext(file.name)[1].lower() if hasattr(file, "name") else ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        for chunk in file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        df = _parse_file(tmp_path)
        df.columns = [
            re.sub(r'[^\w]', '', col.strip().lower().replace(" ", "_").replace("-", "_"))
            or f"col_{i}"
            for i, col in enumerate(df.columns)
        ]

        src_type, src_id = resolve_source(source_str)

        if src_type == "local":
            return _import_local(df, table_name, mode, key_column)
        else:
            return _import_external(df, source_str, table_name, mode, key_column)
    finally:
        os.unlink(tmp_path)


def _import_local(df, table_name, mode, key_column):
    """Import into the local Nexivo database using Django's connection."""
    warnings = []
    with django_connection.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = %s)",
            [table_name],
        )
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            _create_table(cursor, df, table_name)
            warnings.append(f"Table '{table_name}' was created.")
        elif mode == "replace":
            cursor.execute(f'TRUNCATE TABLE "{table_name}"')

    if mode == "upsert" and key_column:
        # Upsert needs a transaction for ON COMMIT DROP temp table
        with transaction.atomic():
            with django_connection.cursor() as cursor:
                rows = _upsert(cursor, df, table_name, key_column)
    else:
        with django_connection.cursor() as cursor:
            rows = _copy_data(cursor, df, table_name)

    return {"rows_affected": rows, "warnings": warnings}


def _import_external(df, source_str, table_name, mode, key_column):
    """Import into an external PostgreSQL database."""
    src_type, src_id = resolve_source(source_str)
    from apps.db_manager.models import ExternalDatabase
    import psycopg2
    ext_db = ExternalDatabase.objects.get(pk=src_id, is_active=True)
    conn = psycopg2.connect(**ext_db.get_connection_params())

    warnings = []
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = %s)",
                [table_name],
            )
            table_exists = cursor.fetchone()[0]

            if not table_exists:
                _create_table(cursor, df, table_name)
                warnings.append(f"Table '{table_name}' was created.")
            elif mode == "replace":
                cursor.execute(f'TRUNCATE TABLE "{table_name}"')

            if mode == "upsert" and key_column:
                rows = _upsert(cursor, df, table_name, key_column)
            else:
                rows = _copy_data(cursor, df, table_name)

        conn.commit()
        return {"rows_affected": rows, "warnings": warnings}
    finally:
        conn.close()


def import_to_new_table(file, source_str, table_name):
    """Import a file into a brand-new table (always creates fresh)."""
    return import_file(file, source_str, table_name, mode="replace")


def _parse_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path, engine="openpyxl")
    elif ext == ".csv":
        return pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _create_table(cursor, df, table_name):
    columns = []
    for col in df.columns:
        pg_type = PG_TYPE_MAP.get(str(df[col].dtype), "TEXT")
        columns.append(f'"{col}" {pg_type}')
    cursor.execute(
        f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(columns)})'
    )


def _copy_data(cursor, df, table_name):
    from io import StringIO
    buffer = StringIO()
    df_clean = df.where(pd.notnull(df), None)
    df_clean.to_csv(buffer, index=False, header=False, sep="\t")
    buffer.seek(0)

    col_list = ['"' + col + '"' for col in df.columns]
    cols_str = ", ".join(col_list)
    copy_sql = (
        f'COPY "{table_name}" ({cols_str}) FROM STDIN '
        f"WITH (FORMAT csv, DELIMITER E'\\t', NULL '')"
    )
    cursor.copy_expert(copy_sql, buffer)
    return len(df)


def _upsert(cursor, df, table_name, key_column):
    """Upsert using a temp table and INSERT ON CONFLICT."""
    temp_table = f"_upsert_temp_{table_name}"

    # Create temp table (ON COMMIT DROP ensures cleanup within a transaction)
    columns = []
    for col in df.columns:
        pg_type = PG_TYPE_MAP.get(str(df[col].dtype), "TEXT")
        columns.append(f'"{col}" {pg_type}')
    cursor.execute(
        f'CREATE TEMP TABLE "{temp_table}" ({", ".join(columns)}) ON COMMIT DROP'
    )

    # Copy data into temp table
    from io import StringIO
    buffer = StringIO()
    df_clean = df.where(pd.notnull(df), None)
    df_clean.to_csv(buffer, index=False, header=False, sep="\t")
    buffer.seek(0)
    col_list = ['"' + col + '"' for col in df.columns]
    cols_str = ", ".join(col_list)
    copy_sql = (
        f'COPY "{temp_table}" ({cols_str}) FROM STDIN '
        f"WITH (FORMAT csv, DELIMITER E'\\t', NULL '')"
    )
    cursor.copy_expert(copy_sql, buffer)

    # Build upsert
    all_cols = ", ".join([f'"{c}"' for c in df.columns])
    update_cols = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in df.columns if c != key_column])

    cursor.execute(
        f'INSERT INTO "{table_name}" ({all_cols}) '
        f'SELECT {all_cols} FROM "{temp_table}" '
        f'ON CONFLICT ("{key_column}") DO UPDATE SET {update_cols}'
    )
    return len(df)
