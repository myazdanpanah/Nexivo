import logging

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
    DashboardPageExportSerializer,
)


# ---- Dashboard Templates ----

DASHBOARD_TEMPLATES = {
    "sales": {
        "name": "داشبورد فروش",
        "description": "پیگیری عملکرد فروش، درآمد، و معاملات",
        "pages": [
            {
                "name": "نمای کلی فروش",
                "widgets": [
                    {"title": "درآمد کل", "chart_type": "kpi", "grid_x": 0, "grid_y": 0, "grid_w": 3, "grid_h": 3},
                    {"title": "تعداد معاملات", "chart_type": "kpi", "grid_x": 3, "grid_y": 0, "grid_w": 3, "grid_h": 3},
                    {"title": "میانگین معامله", "chart_type": "kpi", "grid_x": 6, "grid_y": 0, "grid_w": 3, "grid_h": 3},
                    {"title": "نرخ برد", "chart_type": "kpi", "grid_x": 9, "grid_y": 0, "grid_w": 3, "grid_h": 3},
                    {"title": "روند درآمد", "chart_type": "line", "grid_x": 0, "grid_y": 3, "grid_w": 8, "grid_h": 5},
                    {"title": "فروش بر اساس منطقه", "chart_type": "pie", "grid_x": 8, "grid_y": 3, "grid_w": 4, "grid_h": 5},
                ],
            },
            {
                "name": "جزئیات فروش",
                "widgets": [
                    {"title": "جدول معاملات", "chart_type": "table", "grid_x": 0, "grid_y": 0, "grid_w": 12, "grid_h": 6},
                ],
            },
        ],
    },
    "finance": {
        "name": "داشبورد مالی",
        "description": "پیگیری بودجه، هزینه‌ها، و سود و زیان",
        "pages": [
            {
                "name": "نمای کلی مالی",
                "widgets": [
                    {"title": "درآمد خالص", "chart_type": "kpi", "grid_x": 0, "grid_y": 0, "grid_w": 4, "grid_h": 3},
                    {"title": "هزینه‌ها", "chart_type": "kpi", "grid_x": 4, "grid_y": 0, "grid_w": 4, "grid_h": 3},
                    {"title": "سود خالص", "chart_type": "kpi", "grid_x": 8, "grid_y": 0, "grid_w": 4, "grid_h": 3},
                    {"title": "روند سود و زیان", "chart_type": "area", "grid_x": 0, "grid_y": 3, "grid_w": 8, "grid_h": 5},
                    {"title": "توزیع هزینه‌ها", "chart_type": "donut", "grid_x": 8, "grid_y": 3, "grid_w": 4, "grid_h": 5},
                ],
            },
        ],
    },
    "marketing": {
        "name": "داشبورد بازاریابی",
        "description": "پیگیری کمپین‌ها، ترافیک، و نرخ تبدیل",
        "pages": [
            {
                "name": "نمای کلی بازاریابی",
                "widgets": [
                    {"title": "ترافیک وب", "chart_type": "kpi", "grid_x": 0, "grid_y": 0, "grid_w": 3, "grid_h": 3},
                    {"title": "نرخ تبدیل", "chart_type": "kpi", "grid_x": 3, "grid_y": 0, "grid_w": 3, "grid_h": 3},
                    {"title": "هزینه هر مشتری", "chart_type": "kpi", "grid_x": 6, "grid_y": 0, "grid_w": 3, "grid_h": 3},
                    {"title": "ROI کمپین", "chart_type": "kpi", "grid_x": 9, "grid_y": 0, "grid_w": 3, "grid_h": 3},
                    {"title": "روند ترافیک", "chart_type": "line", "grid_x": 0, "grid_y": 3, "grid_w": 8, "grid_h": 5},
                    {"title": "منابع ترافیک", "chart_type": "pie", "grid_x": 8, "grid_y": 3, "grid_w": 4, "grid_h": 5},
                ],
            },
        ],
    },
    "hr": {
        "name": "داشبورد منابع انسانی",
        "description": "پیگیری کارکنان، جذب نیرو، و رضایت",
        "pages": [
            {
                "name": "نمای کلی کارکنان",
                "widgets": [
                    {"title": "تعداد کل کارکنان", "chart_type": "kpi", "grid_x": 0, "grid_y": 0, "grid_w": 4, "grid_h": 3},
                    {"title": "نرخ جابجایی", "chart_type": "kpi", "grid_x": 4, "grid_y": 0, "grid_w": 4, "grid_h": 3},
                    {"title": "positions باز", "chart_type": "kpi", "grid_x": 8, "grid_y": 0, "grid_w": 4, "grid_h": 3},
                    {"title": "ترکیب تیم‌ها", "chart_type": "pie", "grid_x": 0, "grid_y": 3, "grid_w": 6, "grid_h": 5},
                    {"title": "روند استخدام", "chart_type": "bar", "grid_x": 6, "grid_y": 3, "grid_w": 6, "grid_h": 5},
                ],
            },
        ],
    },
    "retail": {
        "name": "داشبورد خرده‌فروشی",
        "description": "پیگیری فروش، موجودی، و عملکرد محصولات",
        "pages": [
            {
                "name": "نمای کلی فروشگاه",
                "widgets": [
                    {"title": "فروش روزانه", "chart_type": "kpi", "grid_x": 0, "grid_y": 0, "grid_w": 3, "grid_h": 3},
                    {"title": "موجودی", "chart_type": "kpi", "grid_x": 3, "grid_y": 0, "grid_w": 3, "grid_h": 3},
                    {"title": "میانگین سبد خرید", "chart_type": "kpi", "grid_x": 6, "grid_y": 0, "grid_w": 3, "grid_h": 3},
                    {"title": "نرخ بازگشت", "chart_type": "kpi", "grid_x": 9, "grid_y": 0, "grid_w": 3, "grid_h": 3},
                    {"title": "روند فروش", "chart_type": "area", "grid_x": 0, "grid_y": 3, "grid_w": 8, "grid_h": 5},
                    {"title": "محصولات پرفروش", "chart_type": "bar", "grid_x": 8, "grid_y": 3, "grid_w": 4, "grid_h": 5},
                ],
            },
            {
                "name": "موجودی کالاها",
                "widgets": [
                    {"title": "جدول موجودی", "chart_type": "table", "grid_x": 0, "grid_y": 0, "grid_w": 12, "grid_h": 6},
                ],
            },
        ],
    },
    "blank": {
        "name": "داشبورد خالی",
        "description": "شروع از صفر",
        "pages": [
            {
                "name": "صفحه ۱",
                "widgets": [],
            },
        ],
    },
}


@api_view(["GET"])
def dashboard_templates(request):
    """List available dashboard templates."""
    templates = []
    for key, tmpl in DASHBOARD_TEMPLATES.items():
        templates.append({
            "id": key,
            "name": tmpl["name"],
            "description": tmpl["description"],
            "page_count": len(tmpl["pages"]),
            "widget_count": sum(len(p["widgets"]) for p in tmpl["pages"]),
        })
    return Response(templates)


logger = logging.getLogger(__name__)


@api_view(["POST"])
def dashboard_create_from_template(request):
    """Create a dashboard from a template."""
    template_id = request.data.get("template_id")
    if template_id not in DASHBOARD_TEMPLATES:
        logger.warning("Invalid template_id=%s from user=%s", template_id, request.user)
        return Response({"error": "Invalid template"}, status=status.HTTP_400_BAD_REQUEST)

    tmpl = DASHBOARD_TEMPLATES[template_id]
    logger.info("Creating dashboard from template=%s for user=%s", template_id, request.user)

    # Create dashboard
    dashboard = Dashboard.objects.create(
        name=tmpl["name"],
        description=tmpl["description"],
        owner=request.user,
        is_published=True,
        allowed_roles=["ceo", "finance", "sales"],
    )

    # Create pages and widgets
    for page_idx, page_data in enumerate(tmpl["pages"]):
        page = DashboardPage.objects.create(
            dashboard=dashboard,
            name=page_data["name"],
            order=page_idx,
        )

        # Create widgets first, then build layout from their actual IDs
        layout = []
        for idx, widget_data in enumerate(page_data["widgets"]):
            widget = Widget.objects.create(
                dashboard=dashboard,
                page=page,
                title=widget_data["title"],
                chart_type=widget_data["chart_type"],
                grid_x=widget_data.get("grid_x", 0),
                grid_y=widget_data.get("grid_y", 0),
                grid_w=widget_data.get("grid_w", 6),
                grid_h=widget_data.get("grid_h", 4),
                order=idx,
            )
            layout.append({
                "i": str(widget.id),
                "x": widget.grid_x,
                "y": widget.grid_y,
                "w": widget.grid_w,
                "h": widget.grid_h,
            })

        # Update page with correct layout referencing actual widget IDs
        page.layout = layout
        page.save(update_fields=["layout"])

    return Response(
        DashboardSerializer(dashboard).data,
        status=status.HTTP_201_CREATED,
    )


# ---- Dashboard CRUD ----

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
        try:
            page = DashboardPage.objects.get(pk=page_id, dashboard=dashboard)
        except DashboardPage.DoesNotExist:
            return Response({"error": "Page not found"}, status=status.HTTP_404_NOT_FOUND)
        page.layout = layout
        page.save()
    else:
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
        # Enforce per-page access control
        page_roles = page.allowed_roles or []
        if page_roles and request.user.role != "ceo" and not request.user.is_staff:
            if request.user.role not in page_roles:
                return Response(
                    {"error": "You do not have access to this page"},
                    status=status.HTTP_403_FORBIDDEN,
                )
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

    new_page = DashboardPage.objects.create(
        dashboard=dashboard,
        name=f"{source_page.name} (کپی)",
        order=dashboard.pages.count(),
        filter_controls=source_page.filter_controls,
        allowed_roles=source_page.allowed_roles,
    )

    # Remap layout IDs from source widgets to new widgets
    new_layout = []
    source_widgets = list(source_page.widgets.all())
    id_map = {}

    for widget in source_widgets:
        new_widget = Widget.objects.create(
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
        id_map[str(widget.id)] = str(new_widget.id)

    for item in source_page.layout:
        new_item = dict(item)
        new_item["i"] = id_map.get(str(item.get("i", "")), str(item.get("i", "")))
        new_layout.append(new_item)

    new_page.layout = new_layout
    new_page.save(update_fields=["layout"])

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


@api_view(["GET"])
def page_export(request, dashboard_pk, page_pk):
    """Export a page as JSON."""
    try:
        page = DashboardPage.objects.get(pk=page_pk, dashboard_id=dashboard_pk)
    except DashboardPage.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    return Response(DashboardPageExportSerializer(page).data)


@api_view(["POST"])
def page_import(request, dashboard_pk):
    """Import a page from JSON data."""
    try:
        dashboard = Dashboard.objects.get(pk=dashboard_pk)
    except Dashboard.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.user.role != "ceo" and not request.user.is_staff:
        if dashboard.owner != request.user:
            return Response(
                {"error": "Only the owner can import pages"},
                status=status.HTTP_403_FORBIDDEN,
            )

    data = request.data
    page = DashboardPage.objects.create(
        dashboard=dashboard,
        name=data.get("name", "صفحه وارد شده"),
        order=dashboard.pages.count(),
        layout=data.get("layout", []),
        filter_controls=data.get("filter_controls", []),
        allowed_roles=data.get("allowed_roles", []),
    )

    for widget_data in data.get("widgets", []):
        Widget.objects.create(
            dashboard=dashboard,
            page=page,
            title=widget_data.get("title", "نمودار"),
            chart_type=widget_data.get("chart_type", "bar"),
            dataset_id=widget_data.get("dataset"),
            chart_config=widget_data.get("chart_config", {}),
            query_config=widget_data.get("query_config", {}),
            grid_x=widget_data.get("grid_x", 0),
            grid_y=widget_data.get("grid_y", 0),
            grid_w=widget_data.get("grid_w", 6),
            grid_h=widget_data.get("grid_h", 4),
            order=widget_data.get("order", 0),
        )

    return Response(
        DashboardPageSerializer(page).data,
        status=status.HTTP_201_CREATED,
    )


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
