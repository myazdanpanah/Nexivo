"""Database Manager API views."""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import ExternalDatabase, DatabasePermission, GoogleSheetsSync
from .serializers import (
    ExternalDatabaseSerializer,
    ExternalDatabaseCreateSerializer,
    DatabasePermissionSerializer,
    GoogleSheetsSyncSerializer,
    GoogleSheetsSyncCreateSerializer,
)
from apps.datasets.models import Dataset


def _is_admin_or_ceo(user):
    return user.role in ("admin", "ceo") or user.is_staff


def _check_table_perm(user, source, table):
    """Check CanEditTable permission for updater-role users.
    Returns None on OK, Response on denial.
    """
    if user.role in ("admin", "ceo") or user.is_staff:
        return None
    if user.role != "updater":
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    from django.db import models as db_models

    has_perm = DatabasePermission.objects.filter(
        user=user, database_source=source, can_edit=True,
    ).filter(
        db_models.Q(table_name="*") | db_models.Q(table_name=table)
    ).exists()
    if not has_perm:
        return Response({"error": "Permission denied for this table"}, status=status.HTTP_403_FORBIDDEN)
    return None


# ---- Database Management ----


@api_view(["GET", "POST"])
def database_list(request):
    """List all databases (Nexivo datasets + external) or add external DB."""
    if request.method == "GET":
        result = []

        # Local datasets
        datasets = Dataset.objects.filter(status="ready")
        if not (_is_admin_or_ceo(request.user) or request.user.is_staff):
            datasets = datasets.filter(allowed_roles__contains=request.user.role)

        for ds in datasets:
            result.append({
                "id": ds.id,
                "source": "local",
                "name": ds.name,
                "table_name": ds.table_name,
                "type": "dataset",
                "row_count": ds.row_count,
                "column_count": ds.column_count,
                "is_active": True,
            })

        # External databases
        if _is_admin_or_ceo(request.user) or request.user.is_staff:
            ext_dbs = ExternalDatabase.objects.all()
        else:
            ext_dbs = ExternalDatabase.objects.filter(is_active=True)

        for db in ext_dbs:
            result.append({
                "id": db.id,
                "source": f"external_{db.id}",
                "name": db.name,
                "type": "external",
                "host": db.host,
                "database": db.database,
                "is_active": db.is_active,
            })

        return Response(result)

    elif request.method == "POST":
        if not _is_admin_or_ceo(request.user):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ExternalDatabaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        db = serializer.save(owner=request.user)
        return Response(
            ExternalDatabaseSerializer(db).data,
            status=status.HTTP_201_CREATED,
        )


@api_view(["GET", "PUT", "DELETE"])
def database_detail(request, pk):
    """Get, update, or delete an external DB connection."""
    try:
        db = ExternalDatabase.objects.get(pk=pk)
    except ExternalDatabase.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(ExternalDatabaseSerializer(db).data)
    elif request.method == "PUT":
        if not _is_admin_or_ceo(request.user):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ExternalDatabaseCreateSerializer(db, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ExternalDatabaseSerializer(db).data)
    elif request.method == "DELETE":
        if not _is_admin_or_ceo(request.user):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        db.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def database_test(request, pk):
    """Test an external DB connection."""
    try:
        db = ExternalDatabase.objects.get(pk=pk)
    except ExternalDatabase.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    from .services.connection import test_connection
    ok, message = test_connection(db.host, db.port, db.database, db.username, db.password)
    return Response({"ok": ok, "message": message})


# ---- Table Operations ----


@api_view(["GET"])
def table_list(request, source):
    """List tables in a database."""
    from .services.table_ops import list_tables

    try:
        tables = list_tables(source)
        return Response(tables)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def table_schema(request, source, table):
    """Get column names/types for a table."""
    from .services.table_ops import get_table_schema

    try:
        schema = get_table_schema(source, table)
        return Response(schema)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def table_data(request, source, table):
    """Browse rows (paginated) for a table."""
    from .services.table_ops import browse_data

    try:
        offset = int(request.query_params.get("offset", 0))
        limit = int(request.query_params.get("limit", 100))
        order_by = request.query_params.get("order_by")
        order_dir = request.query_params.get("order_dir", "ASC")

        data = browse_data(source, table, offset, limit, order_by, order_dir)
        return Response(data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def table_count(request, source, table):
    """Get row count for a table."""
    from .services.table_ops import count_rows

    try:
        count = count_rows(source, table)
        return Response({"count": count})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ---- Cell Editing ----


@api_view(["PATCH"])
def cell_update(request, source, table):
    """Update a single cell."""
    data = request.data
    pk_column = data.get("pk_column")
    pk_value = data.get("pk_value")
    column = data.get("column")
    value = data.get("value")

    if not all([pk_column, pk_value is not None, column, value is not None]):
        return Response(
            {"error": "pk_column, pk_value, column, and value are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    perm_err = _check_table_perm(request.user, source, table)
    if perm_err:
        return perm_err

    from .services.cell_editor import update_cell

    try:
        rows = update_cell(source, table, pk_column, pk_value, column, value)
        return Response({"rows_affected": rows})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH"])
def batch_update(request, source, table):
    """Batch update cells."""
    updates = request.data.get("updates", [])
    if not updates:
        return Response({"error": "updates list is required"}, status=status.HTTP_400_BAD_REQUEST)

    perm_err = _check_table_perm(request.user, source, table)
    if perm_err:
        return perm_err

    from .services.cell_editor import batch_update as do_batch_update

    try:
        rows = do_batch_update(source, table, updates)
        return Response({"rows_affected": rows})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def row_insert(request, source, table):
    """Insert a new row."""
    perm_err = _check_table_perm(request.user, source, table)
    if perm_err:
        return perm_err

    from .services.cell_editor import insert_row

    try:
        row = insert_row(source, table, request.data)
        return Response(row, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def row_delete(request, source, table):
    """Delete rows by primary key values."""
    pk_column = request.data.get("pk_column")
    pk_values = request.data.get("pk_values", [])

    if not pk_column or not pk_values:
        return Response(
            {"error": "pk_column and pk_values are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    perm_err = _check_table_perm(request.user, source, table)
    if perm_err:
        return perm_err

    from .services.cell_editor import delete_rows

    try:
        rows = delete_rows(source, table, pk_column, pk_values)
        return Response({"rows_affected": rows})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ---- Schema Editing ----


@api_view(["POST"])
def column_add(request, source, table):
    """Add a new column."""
    if not _is_admin_or_ceo(request.user):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    column_name = request.data.get("column_name")
    column_type = request.data.get("column_type", "TEXT")
    default = request.data.get("default")
    nullable = request.data.get("nullable", True)

    if not column_name:
        return Response({"error": "column_name is required"}, status=status.HTTP_400_BAD_REQUEST)

    from .services.schema_editor import add_column

    try:
        add_column(source, table, column_name, column_type, default, nullable)
        return Response({"ok": True}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH"])
def column_update(request, source, table, column_name):
    """Rename or change type of a column."""
    if not _is_admin_or_ceo(request.user):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    from .services.schema_editor import rename_column, change_column_type

    new_name = request.data.get("new_name")
    new_type = request.data.get("new_type")

    try:
        if new_name:
            rename_column(source, table, column_name, new_name)
        if new_type:
            col = new_name or column_name
            change_column_type(source, table, col, new_type)
        return Response({"ok": True})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def column_drop(request, source, table, column_name):
    """Drop a column."""
    if not _is_admin_or_ceo(request.user):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    from .services.schema_editor import drop_column

    try:
        drop_column(source, table, column_name)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ---- File Import ----


@api_view(["POST"])
def file_import(request, source, table):
    """Import a file into an existing table."""
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return Response({"error": "file is required"}, status=status.HTTP_400_BAD_REQUEST)

    mode = request.data.get("mode", "replace")
    key_column = request.data.get("key_column")

    perm_err = _check_table_perm(request.user, source, table)
    if perm_err:
        return perm_err

    from .services.file_import import import_file

    try:
        result = import_file(uploaded_file, source, table, mode, key_column)
        return Response(result)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def file_import_new(request):
    """Import a file to a new table."""
    uploaded_file = request.FILES.get("file")
    table_name = request.data.get("table_name")
    source = request.data.get("source", "local")

    if not uploaded_file:
        return Response({"error": "file is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not table_name:
        return Response({"error": "table_name is required"}, status=status.HTTP_400_BAD_REQUEST)

    from .services.file_import import import_to_new_table

    try:
        result = import_to_new_table(uploaded_file, source, table_name)
        return Response(result, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ---- SQL Editor ----


@api_view(["POST"])
def sql_execute(request):
    """Execute a SQL query (admin/CEO only)."""
    if not _is_admin_or_ceo(request.user):
        return Response({"error": "SQL editor is admin/CEO only"}, status=status.HTTP_403_FORBIDDEN)

    source = request.data.get("source", "local")
    sql = request.data.get("sql", "")
    allow_multi = request.data.get("allow_multi", False)

    from .services.sql_executor import execute_sql

    try:
        result = execute_sql(source, sql, allow_multi)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ---- Google Sheets Sync ----


@api_view(["GET", "POST"])
def sync_list(request):
    """List or create sync configurations."""
    if request.method == "GET":
        if _is_admin_or_ceo(request.user) or request.user.is_staff:
            syncs = GoogleSheetsSync.objects.all()
        else:
            syncs = GoogleSheetsSync.objects.filter(owner=request.user)
        return Response(GoogleSheetsSyncSerializer(syncs, many=True).data)

    elif request.method == "POST":
        if not _is_admin_or_ceo(request.user):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = GoogleSheetsSyncCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sync = serializer.save(owner=request.user)
        return Response(
            GoogleSheetsSyncSerializer(sync).data,
            status=status.HTTP_201_CREATED,
        )


@api_view(["GET", "PUT", "DELETE"])
def sync_detail(request, pk):
    """Get, update, or delete a sync configuration."""
    try:
        sync = GoogleSheetsSync.objects.get(pk=pk)
    except GoogleSheetsSync.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(GoogleSheetsSyncSerializer(sync).data)
    elif request.method == "PUT":
        if not _is_admin_or_ceo(request.user):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = GoogleSheetsSyncCreateSerializer(sync, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(GoogleSheetsSyncSerializer(sync).data)
    elif request.method == "DELETE":
        if not _is_admin_or_ceo(request.user):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        sync.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def sync_run(request, pk):
    """Trigger a manual sync."""
    try:
        sync = GoogleSheetsSync.objects.get(pk=pk)
    except GoogleSheetsSync.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    from .services.sheets_sync import sync_from_sheets

    result = sync_from_sheets(sync)

    from django.utils import timezone
    sync.last_sync_at = timezone.now()
    sync.last_sync_status = result["status"]
    sync.last_error = result.get("error", "")
    sync.save(update_fields=["last_sync_at", "last_sync_status", "last_error"])

    return Response(result)


# ---- Permissions Management ----


@api_view(["GET", "POST"])
def permission_list_create(request):
    """List all permissions (admin only) or grant a new one."""
    if not _is_admin_or_ceo(request.user):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        perms = DatabasePermission.objects.select_related("user").all()
        return Response(DatabasePermissionSerializer(perms, many=True).data)

    elif request.method == "POST":
        serializer = DatabasePermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        perm = serializer.save()
        return Response(
            DatabasePermissionSerializer(perm).data,
            status=status.HTTP_201_CREATED,
        )


@api_view(["DELETE"])
def permission_detail(request, pk):
    """Revoke a permission."""
    if not _is_admin_or_ceo(request.user):
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    try:
        perm = DatabasePermission.objects.get(pk=pk)
    except DatabasePermission.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    perm.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
