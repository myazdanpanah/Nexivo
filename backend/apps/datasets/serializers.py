from rest_framework import serializers
from .models import Dataset, DataFilter


class DataFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataFilter
        fields = ["id", "column_name", "role", "operator", "value", "is_active"]


class DatasetSerializer(serializers.ModelSerializer):
    filters = DataFilterSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Dataset
        fields = [
            "id", "name", "description", "table_name", "status",
            "row_count", "column_count", "column_names", "column_types",
            "allowed_roles", "owner", "owner_name",
            "created_at", "updated_at", "filters",
        ]
        read_only_fields = ["id", "status", "row_count", "column_count", "column_names", "column_types", "superset_dataset_id", "created_at", "updated_at"]


class DatasetUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    allowed_roles = serializers.ListField(
        child=serializers.CharField(),
        default=["ceo"],
    )
