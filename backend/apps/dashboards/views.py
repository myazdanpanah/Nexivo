import logging

from django.db import models
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Dashboard, DashboardPage, Widget, PermissionAuditLog, DashboardAssignment
from .serializers import (
    DashboardSerializer,
    DashboardCreateSerializer,
    WidgetSerializer,
    WidgetCreateSerializer,
    DashboardPageSerializer,
    DashboardPageCreateSerializer,
    DashboardPageExportSerializer,
    DashboardAssignmentSerializer,
    DashboardAssignmentCreateSerializer,
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
        allowed_roles=["ceo", "finance", "sales", "admin"],
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
        if request.user.role in ("ceo", "admin") or request.user.is_staff:
            # CEO/admin sees all published dashboards
            dashboards = Dashboard.objects.filter(is_published=True)
        else:
            # Non-admin: role-based + explicitly assigned dashboards
            role_dashboards = Dashboard.objects.filter(
                is_published=True, allowed_roles__contains=request.user.role
            )
            assigned_ids = DashboardAssignment.objects.filter(
                assigned_to=request.user, is_active=True
            ).values_list("dashboard_id", flat=True)
            assigned_dashboards = Dashboard.objects.filter(
                id__in=assigned_ids, is_published=True
            )
            dashboards = Dashboard.objects.filter(
                models.Q(id__in=role_dashboards) | models.Q(id__in=assigned_dashboards)
            ).distinct()

        serializer = DashboardSerializer(dashboards, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        serializer = DashboardCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dashboard = serializer.save(owner=request.user, is_published=True)
        # Auto-create first page
        DashboardPage.objects.create(dashboard=dashboard, name="صفحه ۱", order=0)
        PermissionAuditLog.objects.create(
            action="dashboard_create",
            user=request.user,
            target_type="dashboard",
            target_id=str(dashboard.pk),
            target_name=dashboard.name,
            new_value={"allowed_roles": dashboard.allowed_roles},
        )
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

    # Allow owner, CEO, admin, or anyone with dashboard access
    if request.user.role != "ceo" and not request.user.is_staff:
        if dashboard.owner != request.user and request.user.role not in dashboard.allowed_roles:
            return Response(
                {"error": "You do not have permission to modify this dashboard"},
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
        if dashboard.owner != request.user and request.user.role not in dashboard.allowed_roles:
            return Response(
                {"error": "You do not have permission to modify this dashboard"},
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
        if dashboard.owner != request.user and request.user.role not in dashboard.allowed_roles:
            return Response(
                {"error": "You do not have permission to modify this dashboard"},
                status=status.HTTP_403_FORBIDDEN,
            )

    serializer = DashboardPageCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if "order" not in serializer.validated_data:
        serializer.validated_data["order"] = dashboard.pages.count()
    page = serializer.save(dashboard=dashboard)
    if page.allowed_roles:
        PermissionAuditLog.objects.create(
            action="page_access_update",
            user=request.user,
            target_type="page",
            target_id=str(page.pk),
            target_name=page.name,
            new_value={"allowed_roles": page.allowed_roles},
            details={"dashboard_id": dashboard_pk},
        )
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
        old_roles = list(page.allowed_roles or [])
        serializer = DashboardPageCreateSerializer(page, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        new_roles = list(page.allowed_roles or [])
        if old_roles != new_roles:
            PermissionAuditLog.objects.create(
                action="page_access_update",
                user=request.user,
                target_type="page",
                target_id=str(page.pk),
                target_name=page.name,
                old_value={"allowed_roles": old_roles},
                new_value={"allowed_roles": new_roles},
                details={"dashboard_id": dashboard_pk},
            )
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
        if dashboard.owner != request.user and request.user.role not in dashboard.allowed_roles:
            return Response(
                {"error": "You do not have permission to modify this dashboard"},
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
        if dashboard.owner != request.user and request.user.role not in dashboard.allowed_roles:
            return Response(
                {"error": "You do not have permission to modify this dashboard"},
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
        if dashboard.owner != request.user and request.user.role not in dashboard.allowed_roles:
            return Response(
                {"error": "You do not have permission to modify this dashboard"},
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
        if dashboard.owner != request.user and request.user.role not in dashboard.allowed_roles:
            return Response(
                {"error": "You do not have permission to modify this dashboard"},
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


# ---- Dashboard Duplicate ----

@api_view(["POST"])
def dashboard_duplicate(request, pk):
    """Duplicate a dashboard with all its pages and widgets."""
    try:
        source = Dashboard.objects.get(pk=pk)
    except Dashboard.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Access check
    if request.user.role != "ceo" and not request.user.is_staff:
        if request.user.role not in source.allowed_roles:
            return Response(
                {"error": "You do not have access to this dashboard"},
                status=status.HTTP_403_FORBIDDEN,
            )

    new_dashboard = Dashboard.objects.create(
        name=f"{source.name} (کپی)",
        description=source.description,
        owner=request.user,
        allowed_roles=source.allowed_roles,
        is_published=True,
        filter_controls=source.filter_controls,
    )

    PermissionAuditLog.objects.create(
        action="dashboard_create",
        user=request.user,
        target_type="dashboard",
        target_id=str(new_dashboard.pk),
        target_name=new_dashboard.name,
        new_value={"allowed_roles": new_dashboard.allowed_roles},
        details={"source_dashboard_id": source.pk},
    )

    # Copy pages and widgets
    for source_page in source.pages.all().order_by("order"):
        new_page = DashboardPage.objects.create(
            dashboard=new_dashboard,
            name=source_page.name,
            order=source_page.order,
            filter_controls=source_page.filter_controls,
            allowed_roles=source_page.allowed_roles,
        )

        id_map = {}
        for widget in source_page.widgets.all():
            new_widget = Widget.objects.create(
                dashboard=new_dashboard,
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

        # Remap layout IDs
        new_layout = []
        for item in source_page.layout:
            new_item = dict(item)
            new_item["i"] = id_map.get(str(item.get("i", "")), str(item.get("i", "")))
            new_layout.append(new_item)
        new_page.layout = new_layout
        new_page.save(update_fields=["layout"])

    return Response(
        DashboardSerializer(new_dashboard).data,
        status=status.HTTP_201_CREATED,
    )


# ---- Dashboard Share ----

@api_view(["PUT"])
def dashboard_share(request, pk):
    """Update allowed_roles for a dashboard (share with roles)."""
    try:
        dashboard = Dashboard.objects.get(pk=pk)
    except Dashboard.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Only owner, CEO, or admin can share
    if request.user.role not in ("ceo", "admin") and not request.user.is_staff:
        if dashboard.owner != request.user:
            return Response(
                {"error": "Only the owner can share this dashboard"},
                status=status.HTTP_403_FORBIDDEN,
            )

    allowed_roles = request.data.get("allowed_roles")
    if allowed_roles is None:
        return Response(
            {"error": "allowed_roles is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    old_roles = list(dashboard.allowed_roles)
    dashboard.allowed_roles = allowed_roles
    dashboard.save(update_fields=["allowed_roles"])

    # Audit log
    PermissionAuditLog.objects.create(
        action="dashboard_share",
        user=request.user,
        target_type="dashboard",
        target_id=str(dashboard.pk),
        target_name=dashboard.name,
        old_value={"allowed_roles": old_roles},
        new_value={"allowed_roles": allowed_roles},
    )

    return Response(DashboardSerializer(dashboard).data)


# ---- Audit Log ----

@api_view(["GET"])
def audit_log_list(request):
    """List audit log entries (admin/CEO only)."""
    if request.user.role not in ("admin", "ceo") and not request.user.is_staff:
        return Response(
            {"error": "Permission denied"},
            status=status.HTTP_403_FORBIDDEN,
        )

    logs = PermissionAuditLog.objects.select_related("user").all()[:100]
    data = []
    for log in logs:
        data.append({
            "id": log.id,
            "action": log.action,
            "action_display": log.get_action_display(),
            "user": log.user.username if log.user else None,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "target_name": log.target_name,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "details": log.details,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })
    return Response(data)


# ---- Dashboard Assignments ----

@api_view(["GET", "POST"])
def assignment_list_create(request):
    """List assignments (for a dashboard or all for admin) or create a new one."""
    if request.user.role not in ("admin", "ceo") and not request.user.is_staff:
        # Managers can see/assign dashboards they own
        pass

    if request.method == "GET":
        dashboard_id = request.query_params.get("dashboard_id")
        user_id = request.query_params.get("user_id")

        assignments = DashboardAssignment.objects.select_related(
            "dashboard", "assigned_to", "assigned_by"
        ).all()

        # Non-admin users only see their own assignments
        if request.user.role not in ("admin", "ceo") and not request.user.is_staff:
            assignments = assignments.filter(
                models.Q(assigned_to=request.user) | models.Q(assigned_by=request.user)
            )

        if dashboard_id:
            assignments = assignments.filter(dashboard_id=dashboard_id)
        if user_id:
            assignments = assignments.filter(assigned_to_id=user_id)

        serializer = DashboardAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        # Only admin, CEO, or dashboard owner can create assignments
        data = request.data.copy()
        dashboard_id = data.get("dashboard")
        try:
            dashboard = Dashboard.objects.get(pk=dashboard_id)
        except Dashboard.DoesNotExist:
            return Response({"error": "Dashboard not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role not in ("admin", "ceo") and not request.user.is_staff:
            if dashboard.owner != request.user:
                return Response(
                    {"error": "Only the dashboard owner or admin can create assignments"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        data["assigned_by"] = request.user.id
        serializer = DashboardAssignmentCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save(assigned_by=request.user)

        # Audit log
        PermissionAuditLog.objects.create(
            action="dashboard_share",
            user=request.user,
            target_type="assignment",
            target_id=str(assignment.pk),
            target_name=f"{dashboard.name} → {assignment.assigned_to.username}",
            new_value={
                "data_filters": assignment.data_filters,
                "visible_pages": assignment.visible_pages,
            },
        )

        return Response(
            DashboardAssignmentSerializer(assignment).data,
            status=status.HTTP_201_CREATED,
        )


@api_view(["GET", "PUT", "DELETE"])
def assignment_detail(request, pk):
    """Retrieve, update, or delete an assignment."""
    try:
        assignment = DashboardAssignment.objects.select_related(
            "dashboard", "assigned_to", "assigned_by"
        ).get(pk=pk)
    except DashboardAssignment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Permission check
    if request.user.role not in ("admin", "ceo") and not request.user.is_staff:
        if assignment.assigned_by != request.user and assignment.assigned_to != request.user:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

    if request.method == "GET":
        return Response(DashboardAssignmentSerializer(assignment).data)

    elif request.method == "PUT":
        if request.user.role not in ("admin", "ceo") and not request.user.is_staff:
            if assignment.assigned_by != request.user:
                return Response(
                    {"error": "Only the assigner can modify this assignment"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        old_filters = list(assignment.data_filters)
        old_pages = list(assignment.visible_pages)

        serializer = DashboardAssignmentCreateSerializer(
            assignment, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save()

        # Audit log if filters changed
        if assignment.data_filters != old_filters or assignment.visible_pages != old_pages:
            PermissionAuditLog.objects.create(
                action="filter_access_update",
                user=request.user,
                target_type="assignment",
                target_id=str(assignment.pk),
                target_name=f"{assignment.dashboard.name} → {assignment.assigned_to.username}",
                old_value={"data_filters": old_filters, "visible_pages": old_pages},
                new_value={
                    "data_filters": assignment.data_filters,
                    "visible_pages": assignment.visible_pages,
                },
            )

        return Response(DashboardAssignmentSerializer(assignment).data)

    elif request.method == "DELETE":
        if request.user.role not in ("admin", "ceo") and not request.user.is_staff:
            if assignment.assigned_by != request.user:
                return Response(
                    {"error": "Only the assigner can delete this assignment"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        assignment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def my_assigned_dashboards(request):
    """List dashboards assigned to the current user."""
    assignments = DashboardAssignment.objects.select_related(
        "dashboard", "assigned_to", "assigned_by"
    ).filter(
        assigned_to=request.user,
        is_active=True,
    )

    result = []
    for assignment in assignments:
        dashboard = assignment.dashboard
        if not dashboard.is_published:
            continue

        # Build per-user data from assignment
        entry = DashboardSerializer(dashboard).data
        entry["assignment_id"] = assignment.pk
        entry["assignment_data_filters"] = assignment.data_filters
        entry["assignment_visible_pages"] = assignment.visible_pages
        entry["assignment_visible_filter_controls"] = assignment.visible_filter_controls
        entry["assigned_by_name"] = (
            assignment.assigned_by.username if assignment.assigned_by else None
        )
        entry["assignment_notes"] = assignment.notes

        # Filter pages based on visible_pages restriction
        if assignment.visible_pages:
            entry["pages"] = [
                p for p in entry.get("pages", [])
                if p["id"] in assignment.visible_pages
            ]

        result.append(entry)

    return Response(result)


# ---- Dashboard Clear All ----

@api_view(["DELETE"])
def dashboard_clear_all(request):
    """Delete all dashboards, pages, and widgets (superuser only)."""
    if not request.user.is_staff:
        return Response(
            {"error": "Only superusers can clear all data"},
            status=status.HTTP_403_FORBIDDEN,
        )

    confirm = request.data.get("confirm")
    if confirm is not True:
        return Response(
            {"error": "Set confirm=true to delete all data"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    widget_count = Widget.objects.count()
    page_count = DashboardPage.objects.count()
    dashboard_count = Dashboard.objects.count()

    Widget.objects.all().delete()
    DashboardPage.objects.all().delete()
    Dashboard.objects.all().delete()

    return Response({
        "deleted": {
            "dashboards": dashboard_count,
            "pages": page_count,
            "widgets": widget_count,
        }
    })
