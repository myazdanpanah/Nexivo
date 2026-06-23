from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Dashboard, DashboardPage, Widget
from .serializers import (
    DashboardSerializer,
    DashboardCreateSerializer,
    WidgetSerializer,
    WidgetCreateSerializer,
    DashboardPageSerializer,
    DashboardPageCreateSerializer,
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
        # Auto-create first page
        DashboardPage.objects.create(dashboard=dashboard, name="صفحه ۱", order=0)
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
    """Update the grid layout of a dashboard page."""
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

    page_id = request.data.get("page_id")
    layout = request.data.get("layout", [])

    if page_id:
        # Page-level layout
        try:
            page = DashboardPage.objects.get(pk=page_id, dashboard=dashboard)
        except DashboardPage.DoesNotExist:
            return Response({"error": "Page not found"}, status=status.HTTP_404_NOT_FOUND)
        page.layout = layout
        page.save()
    else:
        # Dashboard-level layout (legacy)
        dashboard.layout = layout
        dashboard.save()

    # Update widget positions from the layout
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


@api_view(["PUT"])
def dashboard_filter_controls(request, pk):
    """Persist dashboard-level filter controls."""
    try:
        dashboard = Dashboard.objects.get(pk=pk)
    except Dashboard.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.user.role != "ceo" and not request.user.is_staff:
        if dashboard.owner != request.user:
            return Response(
                {"error": "Only the owner can modify filters"},
                status=status.HTTP_403_FORBIDDEN,
            )

    dashboard.filter_controls = request.data.get("filter_controls", [])
    dashboard.save()
    return Response({"filter_controls": dashboard.filter_controls})


# ---- Page endpoints ----

@api_view(["POST"])
def page_create(request, dashboard_pk):
    """Add a page to a dashboard."""
    try:
        dashboard = Dashboard.objects.get(pk=dashboard_pk)
    except Dashboard.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.user.role != "ceo" and not request.user.is_staff:
        if dashboard.owner != request.user:
            return Response(
                {"error": "Only the owner can add pages"},
                status=status.HTTP_403_FORBIDDEN,
            )

    serializer = DashboardPageCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    # Auto-assign order if not provided
    if "order" not in serializer.validated_data:
        serializer.validated_data["order"] = dashboard.pages.count()
    page = serializer.save(dashboard=dashboard)
    return Response(
        DashboardPageSerializer(page).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT", "DELETE"])
def page_detail(request, dashboard_pk, page_pk):
    """Retrieve, update, or delete a page."""
    try:
        page = DashboardPage.objects.get(pk=page_pk, dashboard_id=dashboard_pk)
    except DashboardPage.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(DashboardPageSerializer(page).data)

    elif request.method == "PUT":
        serializer = DashboardPageCreateSerializer(page, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(DashboardPageSerializer(page).data)

    elif request.method == "DELETE":
        page.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def page_duplicate(request, dashboard_pk, page_pk):
    """Duplicate a page with all its widgets."""
    try:
        dashboard = Dashboard.objects.get(pk=dashboard_pk)
    except Dashboard.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.user.role != "ceo" and not request.user.is_staff:
        if dashboard.owner != request.user:
            return Response(
                {"error": "Only the owner can duplicate pages"},
                status=status.HTTP_403_FORBIDDEN,
            )

    try:
        source_page = DashboardPage.objects.get(pk=page_pk, dashboard=dashboard)
    except DashboardPage.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Create new page
    new_page = DashboardPage.objects.create(
        dashboard=dashboard,
        name=f"{source_page.name} (کپی)",
        order=dashboard.pages.count(),
        layout=source_page.layout,
        filter_controls=source_page.filter_controls,
    )

    # Duplicate all widgets on this page
    source_widgets = source_page.widgets.all()
    for widget in source_widgets:
        Widget.objects.create(
            dashboard=dashboard,
            page=new_page,
            title=widget.title,
            chart_type=widget.chart_type,
            dataset=widget.dataset,
            chart_config=widget.chart_config,
            query_config=widget.query_config,
            grid_x=widget.grid_x,
            grid_y=widget.grid_y,
            grid_w=widget.grid_w,
            grid_h=widget.grid_h,
            order=widget.order,
        )

    return Response(
        DashboardPageSerializer(new_page).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["PUT"])
def page_reorder(request, dashboard_pk):
    """Reorder pages in a dashboard."""
    try:
        dashboard = Dashboard.objects.get(pk=dashboard_pk)
    except Dashboard.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.user.role != "ceo" and not request.user.is_staff:
        if dashboard.owner != request.user:
            return Response(
                {"error": "Only the owner can reorder pages"},
                status=status.HTTP_403_FORBIDDEN,
            )

    page_ids = request.data.get("page_ids", [])
    for idx, page_id in enumerate(page_ids):
        try:
            page = DashboardPage.objects.get(pk=page_id, dashboard=dashboard)
            page.order = idx
            page.save(update_fields=["order"])
        except DashboardPage.DoesNotExist:
            continue

    return Response(DashboardSerializer(dashboard).data)


# ---- Widget endpoints ----

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
