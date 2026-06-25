from django.db import models
from django.conf import settings


class Dashboard(models.Model):
    """
    A dashboard is a collection of pages, each containing widgets (charts)
    arranged in a grid layout.
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboards",
    )

    # Grid layout stored as JSON: [{i, x, y, w, h}, ...]
    layout = models.JSONField(default=list, blank=True)

    # Dashboard-level access control
    allowed_roles = models.JSONField(
        default=list,
        blank=True,
        help_text='Roles that can view this dashboard',
    )
    is_published = models.BooleanField(default=False)

    # Dashboard-level filter controls (Looker Studio-style, persisted as JSON)
    filter_controls = models.JSONField(
        default=list,
        blank=True,
        help_text='Persisted dashboard-level filter controls',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


class DashboardPage(models.Model):
    """
    A page within a dashboard. Each page has its own layout and widgets.
    """

    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name="pages")
    name = models.CharField(max_length=255, default="صفحه ۱")
    order = models.IntegerField(default=0)

    # Grid layout for this page
    layout = models.JSONField(default=list, blank=True)

    # Page-level filter controls (Looker Studio-style, persisted as JSON)
    filter_controls = models.JSONField(
        default=list,
        blank=True,
        help_text='Persisted page-level filter controls',
    )

    # Page-level access control
    allowed_roles = models.JSONField(
        default=list,
        blank=True,
        help_text='Roles that can view this page (empty = same as dashboard)',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.name} ({self.dashboard.name})"


class Widget(models.Model):
    """
    A widget is a single chart within a dashboard.
    It stores the chart type, configuration, and data source reference.
    """

    CHART_TYPES = [
        ("bar", "Bar Chart"),
        ("stacked_bar", "Stacked Bar"),
        ("line", "Line Chart"),
        ("area", "Area Chart"),
        ("pie", "Pie Chart"),
        ("donut", "Donut Chart"),
        ("scatter", "Scatter Plot"),
        ("gauge", "Gauge Chart"),
        ("table", "Data Table"),
        ("kpi", "KPI Card"),
        ("heatmap", "Heatmap"),
        ("treemap", "Tree Map"),
        ("sankey", "Sankey Diagram"),
        ("funnel", "Funnel Chart"),
        ("radar", "Radar Chart"),
        ("graph", "Graph/Network"),
        ("map", "Map"),
    ]

    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name="widgets")
    page = models.ForeignKey(
        DashboardPage,
        on_delete=models.CASCADE,
        related_name="widgets",
        null=True,
        blank=True,
        help_text='Page this widget belongs to (null = first page for backward compat)',
    )
    title = models.CharField(max_length=255, default="Untitled Widget")
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES, default="bar")

    # Data source
    dataset = models.ForeignKey(
        "datasets.Dataset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="widgets",
    )

    # ECharts configuration (stored as JSON)
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="ECharts option object for rendering",
    )

    # Query configuration (what data to fetch)
    query_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Columns, metrics, and filters for data fetching",
    )

    # Grid position (react-grid-layout compatible)
    grid_x = models.IntegerField(default=0)
    grid_y = models.IntegerField(default=0)
    grid_w = models.IntegerField(default=6)
    grid_h = models.IntegerField(default=4)

    # Display order
    order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "grid_y", "grid_x"]

    def __str__(self):
        return f"{self.title} ({self.chart_type})"


class PermissionAuditLog(models.Model):
    """
    Tracks permission-related changes on dashboards, pages, and filters.
    """

    ACTION_CHOICES = [
        ("dashboard_share", "Dashboard Share"),
        ("dashboard_create", "Dashboard Create"),
        ("dashboard_delete", "Dashboard Delete"),
        ("page_access_update", "Page Access Update"),
        ("filter_access_update", "Filter Access Update"),
        ("user_role_change", "User Role Change"),
    ]

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    # What was changed
    target_type = models.CharField(
        max_length=50,
        help_text="Type of object: dashboard, page, filter_control, user",
    )
    target_id = models.CharField(
        max_length=100,
        help_text="ID of the affected object",
    )
    target_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Human-readable name of the affected object",
    )
    # Details
    old_value = models.JSONField(
        default=dict,
        blank=True,
        help_text="Previous allowed_roles value",
    )
    new_value = models.JSONField(
        default=dict,
        blank=True,
        help_text="New allowed_roles value",
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} by {self.user} on {self.target_type}:{self.target_id}"
