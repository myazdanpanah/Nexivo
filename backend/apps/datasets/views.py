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


@api_view(["POST"])
def dataset_query(request, pk):
    """
    Query dataset with role-based filters applied.
    Returns chart-ready data.
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
    metrics = request.data.get("metrics", [])
    additional_filters = request.data.get("filters", [])

    # Validate requested columns against dataset schema to prevent SQL injection
    valid_columns = set(dataset.column_names)
    columns = [c for c in requested_columns if c in valid_columns]
    if not columns:
        return Response(
            {"error": "No valid columns requested"},
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

    # TODO: Forward to Superset Chart Data API
    # For now, query directly from PostgreSQL
    from django.db import connection

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

    where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"
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
        "filters_applied": [f.filter_name for f in filters],
    })
