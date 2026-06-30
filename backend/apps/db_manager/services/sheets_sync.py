"""Google Sheets pull and sync logic."""

import io
import pandas as pd
from django.db import connection as django_connection
from .connection import resolve_source


def sync_from_sheets(sync_config):
    """
    Pull data from Google Sheets and sync to a PostgreSQL table.

    Args:
        sync_config: GoogleSheetsSync model instance.

    Returns:
        dict with status, rows_affected, error.
    """
    try:
        df = _fetch_sheet(sync_config.spreadsheet_id, sync_config.sheet_name, sync_config.credentials_json)
        if df.empty:
            return {"status": "success", "rows_affected": 0, "error": ""}

        src_type, src_id = resolve_source(sync_config.database_source)
        conn, close = _get_conn(src_type, src_id)

        try:
            if sync_config.sync_mode == 'upsert' and close:
                # External DB: _sync_upsert_external handles its own transaction
                _sync_upsert_external(conn, df, sync_config)
                rows = len(df)
            elif sync_config.sync_mode == 'upsert' and not close:
                # Local DB: need transaction.atomic() so ON COMMIT DROP works
                from django.db import transaction as db_transaction
                with db_transaction.atomic():
                    with conn.cursor() as cursor:
                        rows = _upsert(cursor, df, sync_config.table_name, sync_config.key_column)
            else:
                # Replace mode (both local and external)
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                        "WHERE table_schema = 'public' AND table_name = %s)",
                        [sync_config.table_name],
                    )
                    table_exists = cursor.fetchone()[0]
                    if table_exists:
                        cursor.execute(f'TRUNCATE TABLE "{sync_config.table_name}"')
                    _copy_data(cursor, df, sync_config.table_name)
                    rows = len(df)

            # External upsert already committed; only commit for replace mode
            if close and sync_config.sync_mode != 'upsert':
                conn.commit()

            return {"status": "success", "rows_affected": rows, "error": ""}
        finally:
            if close:
                conn.close()

    except Exception as e:
        return {"status": "error", "rows_affected": 0, "error": str(e)}


def _sync_upsert_external(conn, df, sync_config):
    """Run upsert for external DB inside an explicit transaction."""
    try:
        with conn.cursor() as cursor:
            cursor.execute('BEGIN')
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = %s)",
                [sync_config.table_name],
            )
            table_exists = cursor.fetchone()[0]
            if not table_exists:
                cursor.execute('COMMIT')
                return
            _upsert(cursor, df, sync_config.table_name, sync_config.key_column)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _fetch_sheet(spreadsheet_id, sheet_name, credentials_json):
    """Fetch data from Google Sheets using a service account."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_info(
        credentials_json,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = build("sheets", "v4", credentials=creds)

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=sheet_name,
    ).execute()

    values = result.get("values", [])
    if not values:
        return pd.DataFrame()

    header = values[0]
    rows = values[1:]
    return pd.DataFrame(rows, columns=header)


PG_TYPE_MAP = {
    "int64": "BIGINT",
    "float64": "DOUBLE PRECISION",
    "object": "TEXT",
    "bool": "BOOLEAN",
    "datetime64[ns]": "TIMESTAMP",
}


def _copy_data(cursor, df, table_name):
    """Create table if needed and copy data."""
    # Create table
    columns = []
    for col in df.columns:
        pg_type = PG_TYPE_MAP.get(str(df[col].dtype), "TEXT")
        columns.append(f'"{col}" {pg_type}')
    cursor.execute(
        f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(columns)})'
    )

    # Copy
    buffer = io.StringIO()
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
    temp_table = f"_sync_temp_{table_name}"

    columns = []
    for col in df.columns:
        pg_type = PG_TYPE_MAP.get(str(df[col].dtype), "TEXT")
        columns.append(f'"{col}" {pg_type}')
    cursor.execute(
        f'CREATE TEMP TABLE IF NOT EXISTS "{temp_table}" ({", ".join(columns)}) ON COMMIT DROP'
    )

    buffer = io.StringIO()
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

    all_cols = ", ".join([f'"{c}"' for c in df.columns])
    update_cols = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in df.columns if c != key_column])

    cursor.execute(
        f'INSERT INTO "{table_name}" ({all_cols}) '
        f'SELECT {all_cols} FROM "{temp_table}" '
        f'ON CONFLICT ("{key_column}") DO UPDATE SET {update_cols}'
    )
    return len(df)


def _get_conn(src_type, src_id):
    if src_type == "local":
        return django_connection, False
    from apps.db_manager.models import ExternalDatabase
    import psycopg2
    ext_db = ExternalDatabase.objects.get(pk=src_id, is_active=True)
    return psycopg2.connect(**ext_db.get_connection_params()), True
