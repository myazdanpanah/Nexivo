from rest_framework import serializers
from .models import Dashboard, Widget


class WidgetSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source="dataset.name", read_only=True, default=None)

    class Meta:
        model = Widget
        fields = [
            "id", "title", "chart_type", "dataset", "dataset_name",
            "chart_config", "query_config",
            "grid_x", "grid_y", "grid_w", "grid_h",
            "order", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DashboardSerializer(serializers.ModelSerializer):
    widgets = WidgetSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Dashboard
        fields = [
            "id", "name", "description", "owner", "owner_name",
            "layout", "allowed_roles", "is_published",
            "widgets", "created_at", "updated_at",
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
            "title", "chart_type", "dataset",
            "chart_config", "query_config",
            "grid_x", "grid_y", "grid_w", "grid_h", "order",
        ]
