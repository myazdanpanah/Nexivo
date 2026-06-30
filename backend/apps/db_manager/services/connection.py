"""Database connection management — local Nexivo DB and external PostgreSQL."""

from contextlib import contextmanager
from django.db import connection as django_connection


def get_local_connection():
    """Return a psycopg2 connection to the local Nexivo database."""
    return django_connection


def get_external_connection(external_db):
    """Open a psycopg2 connection to an ExternalDatabase instance and yield it."""
    import psycopg2

    params = external_db.get_connection_params()
    conn = psycopg2.connect(**params)
    try:
        yield conn
    finally:
        conn.close()


def resolve_source(source_str):
    """
    Parse a source string and return (connection_type, source_id_or_none).

    Returns:
        ("local", None)         — Nexivo's own database
        ("external", ext_db_id)  — External database with given PK
    """
    if source_str == "local":
        return "local", None
    if source_str.startswith("external_"):
        try:
            ext_id = int(source_str.split("_", 1)[1])
            return "external", ext_id
        except (ValueError, IndexError):
            raise ValueError(f"Invalid external source: {source_str}")
    raise ValueError(f"Unknown source: {source_str}")


def get_connection_for_source(source_str):
    """
    Context manager: yield a psycopg2 connection for the given source string.

    For "local" we reuse Django's connection (caller must be in a request context).
    For "external_<id>" we open a fresh psycopg2 connection.
    """
    src_type, src_id = resolve_source(source_str)

    if src_type == "local":
        yield django_connection, False  # not our responsibility to close
    else:
        from apps.db_manager.models import ExternalDatabase

        ext_db = ExternalDatabase.objects.get(pk=src_id, is_active=True)
        import psycopg2

        params = ext_db.get_connection_params()
        conn = psycopg2.connect(**params)
        try:
            yield conn, True  # caller should close
        finally:
            conn.close()


def test_connection(host, port, database, username, password):
    """Test a PostgreSQL connection. Returns (ok: bool, message: str)."""
    import psycopg2

    try:
        conn = psycopg2.connect(
            host=host, port=port, dbname=database,
            user=username, password=password,
            connect_timeout=10,
        )
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        return True, f"Connected: {version}"
    except Exception as e:
        return False, str(e)
