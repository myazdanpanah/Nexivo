import os
import uuid

import pandas as pd
from django.db import connection


def parse_excel_file(file_path: str) -> tuple[pd.DataFrame, list, dict]:
    """
    Parse an Excel file and return the DataFrame, column names, and column types.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path, engine="openpyxl")
    elif ext == ".csv":
        df = pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    # Clean column names: strip whitespace, lowercase, replace spaces/hyphens with underscores,
    # remove ASCII special characters but keep Unicode letters (Farsi, Arabic, etc.)
    import re
    df.columns = [
        re.sub(r'[^\w]', '', col.strip().lower().replace(" ", "_").replace("-", "_"))
        or f"col_{i}"  # fallback for empty names
        for i, col in enumerate(df.columns)
    ]

    # Convert pandas dtypes to PostgreSQL-compatible types
    pg_type_map = {
        "int64": "BIGINT",
        "float64": "DOUBLE PRECISION",
        "object": "TEXT",
        "bool": "BOOLEAN",
        "datetime64[ns]": "TIMESTAMP",
    }

    column_names = list(df.columns)
    column_types = {col: pg_type_map.get(str(dtype), "TEXT") for col, dtype in df.dtypes.items()}

    return df, column_names, column_types


def generate_table_name(original_name: str) -> str:
    """Generate a safe PostgreSQL table name from the dataset name."""
    safe_name = original_name.lower().strip().replace(" ", "_").replace("-", "_")
    # Remove non-alphanumeric characters except underscores
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
    unique_suffix = uuid.uuid4().hex[:8]
    return f"nexivo_data_{safe_name}_{unique_suffix}"


def create_table_from_dataframe(df: pd.DataFrame, table_name: str) -> None:
    """
    Create a PostgreSQL table from a pandas DataFrame.
    Does NOT modify the original data — creates a new table.
    """
    # Map pandas types to PostgreSQL types for SQLAlchemy
    dtype_map = {
        "int64": "BIGINT",
        "float64": "DOUBLE PRECISION",
        "object": "TEXT",
        "bool": "BOOLEAN",
        "datetime64[ns]": "TIMESTAMP",
    }

    # Build CREATE TABLE manually for maximum control
    columns = []
    for col in df.columns:
        pg_type = dtype_map.get(str(df[col].dtype), "TEXT")
        columns.append(f'"{col}" {pg_type}')

    create_sql = f"""
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            {", ".join(columns)}
        );
    """

    with connection.cursor() as cursor:
        cursor.execute(create_sql)
        # TRUNCATE before insert to make idempotent
        cursor.execute(f'TRUNCATE TABLE "{table_name}"')

    # Insert data in chunks
    if not df.empty:
        _insert_dataframe(df, table_name)


def _insert_dataframe(df: pd.DataFrame, table_name: str) -> None:
    """Insert DataFrame rows into a PostgreSQL table using COPY for performance."""
    with connection.cursor() as cursor:
        # Use pandas to_csv for COPY-like performance
        from io import StringIO

        buffer = StringIO()
        # Handle None/NaN values
        df_clean = df.where(pd.notnull(df), None)
        df_clean.to_csv(buffer, index=False, header=False, sep="\t")
        buffer.seek(0)

        col_list = ['"' + col + '"' for col in df.columns]
        cols_str = ", ".join(col_list)
        copy_sql = (
            f'COPY {table_name} ({cols_str}) FROM STDIN '
            f"WITH (FORMAT csv, DELIMITER E'\\t', NULL '')"
        )
        cursor.copy_expert(copy_sql, buffer)


def drop_table(table_name: str) -> None:
    """Drop a table if it exists."""
    import re
    # Validate table name is alphanumeric + underscores only
    if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
        raise ValueError(f"Invalid table name: {table_name}")
    with connection.cursor() as cursor:
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
