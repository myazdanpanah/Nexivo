"""Manufacturing module admin — register models for Django admin."""
from django.contrib import admin
from .models import (
    BOM, BOMLine, Routing, RoutingOperation, WorkCenter,
    ProductionOrder, MaterialConsumption, FinishedGoodsReceipt,
)


class BOMLineInline(admin.TabularInline):
    model = BOMLine
    extra = 0


class RoutingOperationInline(admin.TabularInline):
    model = RoutingOperation
    extra = 0


@admin.register(BOM)
class BOMAdmin(admin.ModelAdmin):
    list_display = ["number", "product_name", "version", "status", "effective_date"]
    list_filter = ["status", "company"]
    search_fields = ["number", "product_name"]
    inlines = [BOMLineInline]


@admin.register(Routing)
class RoutingAdmin(admin.ModelAdmin):
    list_display = ["number", "name", "version", "status"]
    list_filter = ["status", "company"]
    inlines = [RoutingOperationInline]


@admin.register(WorkCenter)
class WorkCenterAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "work_center_type", "capacity", "is_active"]
    list_filter = ["work_center_type", "is_active"]


@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ["number", "product_name", "quantity", "status", "priority"]
    list_filter = ["status", "priority", "company"]
    search_fields = ["number", "product_name"]


@admin.register(MaterialConsumption)
class MaterialConsumptionAdmin(admin.ModelAdmin):
    list_display = ["component_name", "quantity_consumed", "unit_cost", "total_cost", "production_order"]
    list_filter = ["company"]


@admin.register(FinishedGoodsReceipt)
class FinishedGoodsReceiptAdmin(admin.ModelAdmin):
    list_display = ["product_name", "quantity_received", "unit_cost", "total_cost", "production_order"]
    list_filter = ["company"]
