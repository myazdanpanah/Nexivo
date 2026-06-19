from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Dashboard, Widget
from .serializers import (
    DashboardSerializer,
    DashboardCreateSerializer,
    WidgetSerializer,
    WidgetCreateSerializer,
)


@api_view(["GET", "POST"])
def dashboard_list(request):
    """List dashboards or create a new one."""
    if request.method == "GET":
        dashboards = Dashboard.objects.filter(is_published=True)

        # Role-based filtering
        if request.user.role == "ceo" or request.user.is_staff:
            pass  # CEO sees everything
        else:
            dashboards = dashboards.filter(allowed_roles__contains=request.user.role)

        serializer = DashboardSerializer(dashboards, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        serializer = DashboardCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dashboard = serializer.save(owner=request.user)
        return Response(
            DashboardSerializer(dashboard).data,
            status=status.HTTP_201_CREATED,
        )


@api_view(["GET", "PUT", "DELETE"])
def dashboard_detail(request, pk):
    """Retrieve, update, or delete a dashboard."""
    try:
        dashboard = Dashboard.objects.get(pk=pk)
    except Dashboard.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Role check
    if request.user.role != "ceo" and not request.user.is_staff:
        if request.user.role not in dashboard.allowed_roles:
            return Response(
                {"error": "You do not have access to this dashboard"},
                status=status.HTTP_403_FORBIDDEN,
            )

    if request.method == "GET":
        return Response(DashboardSerializer(dashboard).data)

    elif request.method == "PUT":
        serializer = DashboardCreateSerializer(dashboard, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(DashboardSerializer(dashboard).data)

    elif request.method == "DELETE":
        dashboard.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["PUT"])
def dashboard_layout(request, pk):
    """Update the grid layout of a dashboard (for drag-and-drop reordering)."""
    try:
        dashboard = Dashboard.objects.get(pk=pk)
    except Dashboard.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.user.role != "ceo" and not request.user.is_staff:
        if dashboard.owner != request.user:
            return Response(
                {"error": "Only the owner can modify layout"},
                status=status.HTTP_403_FORBIDDEN,
            )

    layout = request.data.get("layout", [])
    dashboard.layout = layout
    dashboard.save()

    # Also update widget positions from the layout
    for item in layout:
        try:
            widget = dashboard.widgets.get(id=item.get("i"))
            widget.grid_x = item.get("x", 0)
            widget.grid_y = item.get("y", 0)
            widget.grid_w = item.get("w", 6)
            widget.grid_h = item.get("h", 4)
            widget.save()
        except Widget.DoesNotExist:
            continue

    return Response(DashboardSerializer(dashboard).data)


@api_view(["POST"])
def widget_create(request, dashboard_pk):
    """Add a widget to a dashboard."""
    try:
        dashboard = Dashboard.objects.get(pk=dashboard_pk)
    except Dashboard.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.user.role != "ceo" and not request.user.is_staff:
        if dashboard.owner != request.user:
            return Response(
                {"error": "Only the owner can add widgets"},
                status=status.HTTP_403_FORBIDDEN,
            )

    serializer = WidgetCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    widget = serializer.save(dashboard=dashboard)
    return Response(
        WidgetSerializer(widget).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT", "DELETE"])
def widget_detail(request, dashboard_pk, widget_pk):
    """Retrieve, update, or delete a widget."""
    try:
        widget = Widget.objects.get(pk=widget_pk, dashboard_id=dashboard_pk)
    except Widget.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(WidgetSerializer(widget).data)

    elif request.method == "PUT":
        serializer = WidgetCreateSerializer(widget, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(WidgetSerializer(widget).data)

    elif request.method == "DELETE":
        widget.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
