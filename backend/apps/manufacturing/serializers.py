"""
Manufacturing Module Serializers — API data transfer objects.
Per API_SPECIFICATION.md §5: Serializer conventions.
"""

from rest_framework import serializers
from .models import (
    BOM, BOMLine, Routing, RoutingOperation, WorkCenter,
    ProductionOrder, MaterialConsumption, FinishedGoodsReceipt,
)


# ─── BOM ───────────────────────────────────────────────────────

class BOMLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOMLine
        fields = [
            "id", "line_number", "component_name", "component_code",
            "quantity", "unit", "unit_cost", "scrap_percentage",
            "consumption_type", "substitute_component", "notes", "kol",
        ]


class BOMSerializer(serializers.ModelSerializer):
    lines = BOMLineSerializer(many=True, read_only=True)
    total_cost = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = BOM
        fields = [
            "id", "number", "product_name", "product_code", "version",
            "revision", "effective_date", "expiry_date", "status",
            "description", "base_quantity", "unit", "total_cost",
            "approved_by", "approved_at", "created_by",
            "created_at", "updated_at", "lines",
        ]
        read_only_fields = ["created_by", "approved_by", "approved_at"]


class BOMCreateSerializer(serializers.ModelSerializer):
    lines = BOMLineSerializer(many=True, required=False)

    class Meta:
        model = BOM
        fields = [
            "number", "product_name", "product_code", "version",
            "revision", "effective_date", "expiry_date", "status",
            "description", "base_quantity", "unit", "lines",
        ]

    def create(self, validated_data):
        lines_data = validated_data.pop("lines", [])
        bom = BOM.objects.create(**validated_data)
        for line_data in lines_data:
            BOMLine.objects.create(bom=bom, **line_data)
        return bom

    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lines_data is not None:
            instance.lines.all().delete()
            for line_data in lines_data:
                BOMLine.objects.create(bom=instance, **line_data)
        return instance


# ─── Routing ───────────────────────────────────────────────────

class RoutingOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingOperation
        fields = [
            "id", "sequence", "code", "name", "description",
            "work_center", "setup_time_minutes", "run_time_minutes",
            "labor_hours", "machine_hours", "is_quality_checkpoint", "notes",
        ]


class RoutingSerializer(serializers.ModelSerializer):
    operations = RoutingOperationSerializer(many=True, read_only=True)

    class Meta:
        model = Routing
        fields = [
            "id", "number", "name", "product_name", "version",
            "status", "description", "estimated_hours",
            "created_by", "created_at", "updated_at", "operations",
        ]
        read_only_fields = ["created_by"]


class RoutingCreateSerializer(serializers.ModelSerializer):
    operations = RoutingOperationSerializer(many=True, required=False)

    class Meta:
        model = Routing
        fields = [
            "number", "name", "product_name", "version",
            "status", "description", "estimated_hours", "operations",
        ]

    def create(self, validated_data):
        operations_data = validated_data.pop("operations", [])
        routing = Routing.objects.create(**validated_data)
        for op_data in operations_data:
            RoutingOperation.objects.create(routing=routing, **op_data)
        return routing


# ─── Work Center ───────────────────────────────────────────────

class WorkCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkCenter
        fields = [
            "id", "code", "name", "work_center_type", "capacity",
            "efficiency", "hourly_cost", "is_active", "description",
            "created_at", "updated_at",
        ]


# ─── Production Order ──────────────────────────────────────────

class ProductionOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionOrder
        fields = [
            "id", "number", "product_name", "product_code", "quantity",
            "unit", "bom", "routing", "start_date_jalali", "end_date_jalali",
            "start_date", "end_date", "status", "priority",
            "material_cost", "labor_cost", "machine_cost", "overhead_cost",
            "total_cost", "journal_voucher", "approved_by", "approved_at",
            "created_by", "description", "created_at", "updated_at",
        ]
        read_only_fields = [
            "created_by", "approved_by", "approved_at", "total_cost",
            "material_cost", "labor_cost", "machine_cost", "overhead_cost",
        ]


# ─── Material Consumption ──────────────────────────────────────

class MaterialConsumptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialConsumption
        fields = [
            "id", "production_order", "component_name", "component_code",
            "quantity_consumed", "unit", "unit_cost", "total_cost",
            "bom_line", "journal_voucher", "consumed_at", "consumed_by", "notes",
        ]
        read_only_fields = ["total_cost", "consumed_by"]


# ─── Finished Goods Receipt ────────────────────────────────────

class FinishedGoodsReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinishedGoodsReceipt
        fields = [
            "id", "production_order", "product_name", "quantity_received",
            "unit", "unit_cost", "total_cost", "quantity_rejected",
            "journal_voucher", "received_at", "received_by", "notes",
        ]
        read_only_fields = ["total_cost", "received_by"]
