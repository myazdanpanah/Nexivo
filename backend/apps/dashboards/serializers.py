from rest_framework import serializers
from .models import Dashboard, DashboardPage, Widget, DashboardAssignment


class WidgetSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source="dataset.name", read_only=True, default=None)
    column_types = serializers.SerializerMethodField()

    class Meta:
        model = Widget
        fields = [
            "id", "title", "chart_type", "dataset", "dataset_name",
            "chart_config", "query_config",
            "column_types",
            "page",
            "grid_x", "grid_y", "grid_w", "grid_h",
            "order", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_column_types(self, obj):
        if obj.dataset:
            return obj.dataset.column_types or {}
        return {}


class DashboardPageSerializer(serializers.ModelSerializer):
    widgets = WidgetSerializer(many=True, read_only=True)
    filter_controls = serializers.JSONField(required=False, default=list)
    allowed_roles = serializers.JSONField(required=False, default=list)

    class Meta:
        model = DashboardPage
        fields = ["id", "name", "order", "layout", "mobile_layout", "filter_controls", "allowed_roles", "widgets", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DashboardPageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardPage
        fields = ["name", "order", "layout", "mobile_layout", "filter_controls", "allowed_roles"]


class DashboardPageExportSerializer(serializers.ModelSerializer):
    """Serializer for exporting a page with all its widgets as JSON."""
    widgets = WidgetSerializer(many=True, read_only=True)

    class Meta:
        model = DashboardPage
        fields = ["name", "order", "layout", "mobile_layout", "filter_controls", "allowed_roles", "widgets"]


class DashboardSerializer(serializers.ModelSerializer):
    pages = DashboardPageSerializer(many=True, read_only=True)
    widgets = WidgetSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source="owner.username", read_only=True)
    filter_controls = serializers.JSONField(required=False, default=list)

    class Meta:
        model = Dashboard
        fields = [
            "id", "name", "description", "owner", "owner_name",
            "layout", "allowed_roles", "is_published",
            "filter_controls",
            "pages", "widgets",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class DashboardCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = ["name", "description", "allowed_roles", "is_published"]


class WidgetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Widget
        fields = [
            "title", "chart_type", "dataset", "page",
            "chart_config", "query_config",
            "grid_x", "grid_y", "grid_w", "grid_h", "order",
        ]


class DashboardAssignmentSerializer(serializers.ModelSerializer):
    dashboard_name = serializers.CharField(source="dashboard.name", read_only=True)
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    assigned_by_username = serializers.CharField(source="assigned_by.username", read_only=True, default=None)

    class Meta:
        model = DashboardAssignment
        fields = [
            "id", "dashboard", "dashboard_name",
            "assigned_to", "assigned_to_username", "assigned_to_name",
            "assigned_by", "assigned_by_username",
            "data_filters", "visible_pages", "visible_filter_controls",
            "notes", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "assigned_by", "created_at", "updated_at"]

    def get_assigned_to_name(self, obj):
        user = obj.assigned_to
        return f"{user.first_name} {user.last_name}".strip() or user.username


class DashboardAssignmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardAssignment
        fields = [
            "dashboard", "assigned_to",
            "data_filters", "visible_pages", "visible_filter_controls",
            "notes", "is_active",
        ]
