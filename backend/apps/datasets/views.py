import os
import tempfile

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.conf import settings

from .models import Dataset, DataFilter
from apps.dashboards.models import DashboardAssignment
from .serializers import DatasetSerializer, DatasetUploadSerializer
from .parsers import parse_excel_file, generate_table_name, create_table_from_dataframe


@api_view(["GET"])
def dataset_list(request):
    """List datasets accessible to the current user's role."""
    datasets = Dataset.objects.filter(status="ready")

    # Role-based filtering: users only see datasets for their role
    if request.user.role == "ceo" or request.user.is_staff:
        pass  # CEO sees everything
    else:
        datasets = datasets.filter(allowed_roles__contains=request.user.role)

    serializer = DatasetSerializer(datasets, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def dataset_upload(request):
    """Upload an Excel/CSV file and create a dataset."""
    serializer = DatasetUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    file = serializer.validated_data["file"]
    name = serializer.validated_data["name"]
    description = serializer.validated_data.get("description", "")
    allowed_roles = serializer.validated_data.get("allowed_roles", ["ceo"])

    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
        for chunk in file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        # Parse the file
        df, column_names, column_types = parse_excel_file(tmp_path)
        table_name = generate_table_name(name)

        # Create PostgreSQL table from data
        create_table_from_dataframe(df, table_name)

        # Create dataset record
        dataset = Dataset.objects.create(
            name=name,
            description=description,
            original_file=file,
            table_name=table_name,
            status="ready",
            row_count=len(df),
            column_count=len(column_names),
            column_names=column_names,
            column_types=column_types,
            allowed_roles=allowed_roles,
            owner=request.user,
        )

        # TODO: Register dataset in Superset via API
        # from .superset import superset_client
        # superset_dataset_id = superset_client.register_dataset(...)

        return Response(
            DatasetSerializer(dataset).data,
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to process file: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    finally:
        os.unlink(tmp_path)


@api_view(["GET", "PUT", "DELETE"])
def dataset_detail(request, pk):
    """Retrieve, update, or delete a dataset."""
    try:
        dataset = Dataset.objects.get(pk=pk)
    except Dataset.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Role check
    if request.user.role != "ceo" and not request.user.is_staff:
        if request.user.role not in dataset.allowed_roles:
            return Response(
                {"error": "You do not have access to this dataset"},
                status=status.HTTP_403_FORBIDDEN,
            )

    if request.method == "GET":
        return Response(DatasetSerializer(dataset).data)

    elif request.method == "PUT":
        serializer = DatasetSerializer(dataset, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    elif request.method == "DELETE":
        dataset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


AGG_FUNCTIONS = {"SUM", "COUNT", "AVG", "MIN", "MAX", "COUNT_DISTINCT"}
DATE_TRUNC_UNITS = {"year", "quarter", "month", "week", "day", "hour"}

# Column types that support numeric aggregation (SUM, AVG, MIN, MAX)
NUMERIC_PG_TYPES = {
    "BIGINT", "INTEGER", "SMALLINT", "DOUBLE PRECISION",
    "REAL", "NUMERIC", "DECIMAL", "FLOAT", "INT64", "FLOAT64",
}
# COUNT works on any type; these are the only ones that support SUM/AVG/MIN/MAX
AGG_NUMERIC_FUNCTIONS = {"SUM", "AVG", "MIN", "MAX", "COUNT_DISTINCT"}


@api_view(["POST"])
def dataset_query(request, pk):
    """
    Query dataset with role-based filters and optional aggregation.

    Request body:
      columns: ["region", "revenue", "cost"]   # all columns to include
      metrics: {"revenue": "SUM", "cost": "AVG"}  # col -> agg func
      filters: [{col, op, val}, ...]

    When *metrics* is provided the backend generates a GROUP BY query:
      SELECT region, SUM(revenue), AVG(cost) FROM ... GROUP BY region

    When *metrics* is empty/absent it returns raw rows (unchanged behaviour).
    """
    try:
        dataset = Dataset.objects.get(pk=pk)
    except Dataset.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Get role-based filters
    filters = DataFilter.objects.filter(
        dataset=dataset,
        role=request.user.role,
        is_active=True,
    )

    # Build query parameters
    requested_columns = request.data.get("columns", dataset.column_names)
    metrics_map = request.data.get("metrics", {})  # {col: FUNC}
    additional_filters = request.data.get("filters", [])

    # Filter-level role enforcement: if the request includes filterControls with allowedRoles,
    # only apply filters that the current user's role has access to
    filter_controls = request.data.get("filterControls", [])
    if filter_controls:
        user_role = request.user.role
        # Map control type to operator(s)
        TYPE_TO_OP = {
            'dropdown': 'eq',
            'checkbox': 'in',
            'text_search': 'contains',
            'date_range': 'between',
            'slider': 'between',
        }
        for fc in filter_controls:
            fc_roles = fc.get("allowedRoles", [])
            if fc_roles and user_role and user_role not in fc_roles:
                continue  # Skip restricted filters
            fc_type = fc.get("type", "dropdown")
            fc_val = fc.get("value")
            fc_col = fc.get("col")
            if not fc_val or not fc_col:
                continue
            op = TYPE_TO_OP.get(fc_type, "eq")
            # Upgrade eq to in for multi-select values
            if op == "eq" and isinstance(fc_val, list):
                op = "in"
            additional_filters.append({"col": fc_col, "op": op, "val": fc_val})

    # Validate requested columns against dataset schema to prevent SQL injection
    valid_columns = set(dataset.column_names)
    columns = [c for c in requested_columns if c in valid_columns]
    if not columns:
        return Response(
            {"error": "No valid columns requested"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate aggregation function names and column type compatibility
    col_types = dataset.column_types or {}
    for col, func in metrics_map.items():
        if func.upper() not in AGG_FUNCTIONS:
            return Response(
                {"error": f"Invalid aggregation function: {func}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if col not in valid_columns:
            return Response(
                {"error": f"Invalid metric column: {col}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Validate that numeric aggregation functions are only used on numeric columns
        if func.upper() in AGG_NUMERIC_FUNCTIONS:
            pg_type = (col_types.get(col, "") or "").upper()
            if pg_type and pg_type not in NUMERIC_PG_TYPES:
                return Response(
                    {"error": f"Cannot apply {func} to non-numeric column '{col}' (type: {pg_type})"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    # Add role-based filters
    for rf in filters:
        additional_filters.append({
            "col": rf.column_name,
            "op": rf.operator,
            "val": rf.value,
        })

    # Enforce row-level data_filters from dashboard assignments
    # The frontend sends dashboardId in the request; we look up any active
    # assignments for this user on that dashboard and apply their data_filters.
    dashboard_id = request.data.get("dashboardId")
    if dashboard_id:
        assignments = DashboardAssignment.objects.filter(
            dashboard_id=dashboard_id,
            assigned_to=request.user,
            is_active=True,
        )
        for assignment in assignments:
            for f in (assignment.data_filters or []):
                if f.get("col") in valid_columns:
                    additional_filters.append(f)

    # Validate filter column names against dataset schema
    for f in additional_filters:
        if f["col"] not in valid_columns:
            return Response(
                {"error": f"Invalid filter column: {f['col']}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    from django.db import connection

    # Build WHERE clause
    where_clauses = []
    params = []
    for f in additional_filters:
        col = f["col"]
        if f["op"] == "eq":
            where_clauses.append(f'"{col}" = %s')
            params.append(f["val"])
        elif f["op"] == "in":
            placeholders = ", ".join(["%s"] * len(f["val"]))
            where_clauses.append(f'"{col}" IN ({placeholders})')
            params.extend(f["val"])
        elif f["op"] == "contains":
            where_clauses.append(f'"{col}" ILIKE %s')
            params.append(f"%{f['val']}%")
        elif f["op"] == "neq":
            where_clauses.append(f'"{col}" != %s')
            params.append(f["val"])
        elif f["op"] == "gt":
            where_clauses.append(f'"{col}" > %s')
            params.append(f["val"])
        elif f["op"] == "gte":
            where_clauses.append(f'"{col}" >= %s')
            params.append(f["val"])
        elif f["op"] == "lt":
            where_clauses.append(f'"{col}" < %s')
            params.append(f["val"])
        elif f["op"] == "lte":
            where_clauses.append(f'"{col}" <= %s')
            params.append(f["val"])
        elif f["op"] == "between":
            where_clauses.append(f'"{col}" >= %s AND "{col}" <= %s')
            if isinstance(f["val"], (list, tuple)) and len(f["val"]) == 2:
                params.extend(f["val"])
            else:
                params.extend([f["val"], f["val"]])
        elif f["op"] == "starts_with":
            where_clauses.append(f'"{col}" ILIKE %s')
            params.append(f"{f['val']}%")
        elif f["op"] == "ends_with":
            where_clauses.append(f'"{col}" ILIKE %s')
            params.append(f"%{f['val']}")

    where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

    # Date grouping: {"col": "month"} -> DATE_TRUNC('month', col)
    date_truncs = request.data.get("date_truncs", {})  # {col: unit}

    # --- Aggregation (GROUP BY) path ---
    if metrics_map or date_truncs:
        # Only aggregate columns that are in the requested columns list
        cols_set = set(columns)
        metric_cols = [c for c in metrics_map.keys() if c in cols_set]
        dim_cols = [c for c in columns if c not in metric_cols]

        # If no explicit dimensions, two cases:
        #   1) Only date_truncs (no metrics) → use date-truncated cols as dimensions
        #   2) All columns are metrics (e.g. KPI) → no dimensions, aggregate everything
        if not dim_cols:
            if date_truncs and not metric_cols:
                # Date-only grouping: all non-date columns that aren't metrics
                # are dimensions; if none, use date_trunc columns themselves
                dim_cols = list(date_truncs.keys())
            elif columns:
                # All columns are metrics → aggregate with no GROUP BY
                # (e.g., KPI chart: SELECT SUM(revenue), SUM(quantity) FROM ...)
                dim_cols = []

        select_parts = []
        group_by_parts = []
        for c in dim_cols:
            if c in date_truncs and date_truncs[c] in DATE_TRUNC_UNITS:
                unit = date_truncs[c]
                alias = f"{c}_{unit}"
                dt_expr = 'DATE_TRUNC(%s, "%s")' % (unit, c)
                select_parts.append(f'{dt_expr}::DATE AS "{alias}"')
                group_by_parts.append(dt_expr)
            else:
                select_parts.append(f'"{c}"')
                group_by_parts.append(f'"{c}"')
        for col in metric_cols:
            func = metrics_map[col].upper()
            alias = col
            select_parts.append(f'{func}("{col}") AS "{alias}"')

        # Build query — only add GROUP BY if there are dimensions
        if dim_cols:
            group_by = ", ".join(group_by_parts)
            order_by = group_by
            query = (
                f'SELECT {", ".join(select_parts)} '
                f'FROM "{dataset.table_name}" '
                f'WHERE {where_sql} '
                f'GROUP BY {group_by} '
                f'ORDER BY {order_by} '
                f'LIMIT 1000'
            )
        else:
            # No dimensions → global aggregation (e.g. KPI)
            query = (
                f'SELECT {", ".join(select_parts)} '
                f'FROM "{dataset.table_name}" '
                f'WHERE {where_sql} '
                f'LIMIT 1'
            )
    else:
        # --- Raw rows path (unchanged) ---
        cols = ", ".join([f'"{c}"' for c in columns])
        query = f'SELECT {cols} FROM "{dataset.table_name}" WHERE {where_sql} LIMIT 1000'

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]

    data = [dict(zip(col_names, row)) for row in rows]

    return Response({
        "columns": col_names,
        "data": data,
        "row_count": len(data),
        "filters_applied": [f"{f.column_name} {f.operator}={f.value}" for f in filters],
    })
