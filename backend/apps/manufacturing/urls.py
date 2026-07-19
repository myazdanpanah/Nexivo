"""
Manufacturing Module URL Patterns.
Per DJANGO_BACKEND.md §20: URL naming conventions.
"""

from django.urls import path
from . import views

urlpatterns = [
    # BOM
    path("boms/", views.bom_list, name="bom-list"),
    path("boms/<int:pk>/", views.bom_detail, name="bom-detail"),
    path("boms/<int:pk>/approve/", views.bom_approve, name="bom-approve"),

    # Routing
    path("routings/", views.routing_list, name="routing-list"),
    path("routings/<int:pk>/", views.routing_detail, name="routing-detail"),

    # Work Centers
    path("work-centers/", views.work_center_list, name="work-center-list"),
    path("work-centers/<int:pk>/", views.work_center_detail, name="work-center-detail"),

    # Production Orders
    path("production-orders/", views.production_order_list, name="production-order-list"),
    path("production-orders/<int:pk>/", views.production_order_detail, name="production-order-detail"),
    path("production-orders/<int:pk>/approve/", views.production_order_confirm, name="production-order-approve"),
    path("production-orders/<int:pk>/start/", views.production_order_start, name="production-order-start"),
    path("production-orders/<int:pk>/complete/", views.production_order_complete, name="production-order-complete"),

    # Material Consumption
    path("material-consumptions/", views.material_consumption_list, name="material-consumption-list"),

    # Finished Goods Receipt
    path("finished-goods-receipts/", views.finished_goods_receipt_list, name="finished-goods-receipt-list"),

    # Summary
    path("summary/", views.manufacturing_summary, name="manufacturing-summary"),
]
