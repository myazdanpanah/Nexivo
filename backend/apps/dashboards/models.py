from django.db import models
from django.conf import settings


class Dashboard(models.Model):
    """
    A dashboard is a collection of widgets (charts) arranged in a grid layout.
    The layout is stored as JSON compatible with react-grid-layout.
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


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
    ]

    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name="widgets")
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
