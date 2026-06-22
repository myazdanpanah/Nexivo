import os
import tempfile

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.conf import settings

from .models import Dataset, DataFilter
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

    # Validate requested columns against dataset schema to prevent SQL injection
    valid_columns = set(dataset.column_names)
    columns = [c for c in requested_columns if c in valid_columns]
    if not columns:
        return Response(
            {"error": "No valid columns requested"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate aggregation function names
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

    # Add role-based filters
    for rf in filters:
        additional_filters.append({
            "col": rf.column_name,
            "op": rf.operator,
            "val": rf.value,
        })

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
        elif f["op"] == "gt":
            where_clauses.append(f'"{col}" > %s')
            params.append(f["val"])
        elif f["op"] == "lt":
            where_clauses.append(f'"{col}" < %s')
            params.append(f["val"])

    where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

    # Date grouping: {"col": "month"} -> DATE_TRUNC('month', col)
    date_truncs = request.data.get("date_truncs", {})  # {col: unit}

    # --- Aggregation (GROUP BY) path ---
    if metrics_map or date_truncs:
        metric_cols = list(metrics_map.keys())
        dim_cols = [c for c in columns if c not in metric_cols]

        # If no explicit dimensions, use columns not in metrics as dims
        # If ALL columns are metrics, pick the first as dimension
        if not dim_cols and columns:
            dim_cols = [columns[0]]
            metric_cols = [c for c in metric_cols if c != columns[0]]

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

        group_by = ", ".join(group_by_parts)
        order_by = group_by  # order by dimension(s)

        query = (
            f'SELECT {", ".join(select_parts)} '
            f'FROM "{dataset.table_name}" '
            f'WHERE {where_sql} '
            f'GROUP BY {group_by} '
            f'ORDER BY {order_by} '
            f'LIMIT 1000'
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
