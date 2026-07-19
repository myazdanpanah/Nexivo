"""
Manufacturing Module Views — Production lifecycle endpoints.
Per API_SPECIFICATION.md §6-§8: Standard response format.
Per MANUFACTURING_MODULE.md §28: AI Agent must use services, not directly modify.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.permissions import RequireModule
from apps.core.responses import (
    success_response, error_response, business_rule_error,
    not_found_response, forbidden_response,
)

from .models import (
    BOM, BOMLine, Routing, RoutingOperation, WorkCenter,
    ProductionOrder, MaterialConsumption, FinishedGoodsReceipt,
)
from .serializers import (
    BOMSerializer, BOMCreateSerializer, BOMLineSerializer,
    RoutingSerializer, RoutingCreateSerializer, RoutingOperationSerializer,
    WorkCenterSerializer, ProductionOrderSerializer,
    MaterialConsumptionSerializer, FinishedGoodsReceiptSerializer,
)

logger = logging.getLogger(__name__)

# ─── Module gate ──────────────────────────────────────────────
_ManufPerm = RequireModule.for_module("manufacturing")()


def _check_manufacturing_module(request):
    if not _ManufPerm.has_permission(request, None):
        return forbidden_response("Module 'manufacturing' is not enabled for your company")
    return None


# ─── BOM ──────────────────────────────────────────────────────

@api_view(["GET", "POST"])
def bom_list(request):
    """List or create BOMs."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    company = request.user.company
    if request.method == "GET":
        qs = BOM.objects.filter(company=company)
        bom_status = request.query_params.get("status")
        if bom_status:
            qs = qs.filter(status=bom_status)
        return success_response(data=BOMSerializer(qs, many=True).data)
    elif request.method == "POST":
        data = request.data.copy()
        serializer = BOMCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        bom = serializer.save(
            company=company, created_by=request.user,
        )
        return success_response(
            data=BOMSerializer(bom).data,
            message="BOM created",
            http_status_code=status.HTTP_201_CREATED,
        )


@api_view(["GET", "PUT", "DELETE"])
def bom_detail(request, pk):
    """Retrieve, update, or delete a BOM."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    try:
        bom = BOM.objects.get(pk=pk, company=request.user.company)
    except BOM.DoesNotExist:
        return not_found_response("BOM not found")
    if request.method == "GET":
        return success_response(data=BOMSerializer(bom).data)
    elif request.method == "PUT":
        serializer = BOMCreateSerializer(bom, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        bom = serializer.save()
        return success_response(data=BOMSerializer(bom).data)
    elif request.method == "DELETE":
        bom.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def bom_approve(request, pk):
    """Approve a BOM — sets status to active."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    try:
        bom = BOM.objects.get(pk=pk, company=request.user.company)
    except BOM.DoesNotExist:
        return not_found_response("BOM not found")
    if bom.status != "draft":
        return business_rule_error("Only draft BOMs can be approved")
    from django.utils import timezone
    bom.status = "active"
    bom.approved_by = request.user
    bom.approved_at = timezone.now()
    bom.save(update_fields=["status", "approved_by", "approved_at"])
    return success_response(data=BOMSerializer(bom).data, message="BOM approved")


# ─── Routing ──────────────────────────────────────────────────

@api_view(["GET", "POST"])
def routing_list(request):
    """List or create routings."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    company = request.user.company
    if request.method == "GET":
        qs = Routing.objects.filter(company=company)
        return success_response(data=RoutingSerializer(qs, many=True).data)
    elif request.method == "POST":
        data = request.data.copy()
        serializer = RoutingCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        routing = serializer.save(company=company, created_by=request.user)
        return success_response(
            data=RoutingSerializer(routing).data,
            message="Routing created",
            http_status_code=status.HTTP_201_CREATED,
        )


@api_view(["GET", "PUT", "DELETE"])
def routing_detail(request, pk):
    """Retrieve, update, or delete a routing."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    try:
        routing = Routing.objects.get(pk=pk, company=request.user.company)
    except Routing.DoesNotExist:
        return not_found_response("Routing not found")
    if request.method == "GET":
        return success_response(data=RoutingSerializer(routing).data)
    elif request.method == "PUT":
        serializer = RoutingCreateSerializer(routing, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        routing = serializer.save()
        return success_response(data=RoutingSerializer(routing).data)
    elif request.method == "DELETE":
        routing.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Work Centers ─────────────────────────────────────────────

@api_view(["GET", "POST"])
def work_center_list(request):
    """List or create work centers."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    company = request.user.company
    if request.method == "GET":
        qs = WorkCenter.objects.filter(company=company)
        return success_response(data=WorkCenterSerializer(qs, many=True).data)
    elif request.method == "POST":
        data = request.data.copy()
        serializer = WorkCenterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        wc = serializer.save(company=company)
        return success_response(
            data=WorkCenterSerializer(wc).data,
            message="Work center created",
            http_status_code=status.HTTP_201_CREATED,
        )


@api_view(["GET", "PUT", "DELETE"])
def work_center_detail(request, pk):
    """Retrieve, update, or delete a work center."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    try:
        wc = WorkCenter.objects.get(pk=pk, company=request.user.company)
    except WorkCenter.DoesNotExist:
        return not_found_response("Work center not found")
    if request.method == "GET":
        return success_response(data=WorkCenterSerializer(wc).data)
    elif request.method == "PUT":
        serializer = WorkCenterSerializer(wc, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        wc = serializer.save()
        return success_response(data=WorkCenterSerializer(wc).data)
    elif request.method == "DELETE":
        wc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Production Orders ────────────────────────────────────────

@api_view(["GET", "POST"])
def production_order_list(request):
    """List or create production orders."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    company = request.user.company
    if request.method == "GET":
        qs = ProductionOrder.objects.filter(company=company)
        po_status = request.query_params.get("status")
        if po_status:
            qs = qs.filter(status=po_status)
        return success_response(data=ProductionOrderSerializer(qs, many=True).data)
    elif request.method == "POST":
        data = request.data.copy()
        serializer = ProductionOrderSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        po = serializer.save(company=company, created_by=request.user)
        return success_response(
            data=ProductionOrderSerializer(po).data,
            message="Production order created",
            http_status_code=status.HTTP_201_CREATED,
        )


@api_view(["GET", "PUT", "DELETE"])
def production_order_detail(request, pk):
    """Retrieve, update, or delete a production order."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    try:
        po = ProductionOrder.objects.get(pk=pk, company=request.user.company)
    except ProductionOrder.DoesNotExist:
        return not_found_response("Production order not found")
    if request.method == "GET":
        return success_response(data=ProductionOrderSerializer(po).data)
    elif request.method == "PUT":
        serializer = ProductionOrderSerializer(po, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        po = serializer.save()
        return success_response(data=ProductionOrderSerializer(po).data)
    elif request.method == "DELETE":
        po.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def production_order_confirm(request, pk):
    """Approve a production order — sets status to approved."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    try:
        po = ProductionOrder.objects.get(pk=pk, company=request.user.company)
    except ProductionOrder.DoesNotExist:
        return not_found_response("Production order not found")
    if po.status != "draft":
        return business_rule_error("Only draft production orders can be approved")
    from django.utils import timezone
    po.status = "approved"
    po.approved_by = request.user
    po.approved_at = timezone.now()
    po.save(update_fields=["status", "approved_by", "approved_at"])
    return success_response(data=ProductionOrderSerializer(po).data, message="Production order approved")


@api_view(["POST"])
def production_order_start(request, pk):
    """Start production — sets status to started."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    try:
        po = ProductionOrder.objects.get(pk=pk, company=request.user.company)
    except ProductionOrder.DoesNotExist:
        return not_found_response("Production order not found")
    if po.status not in ("approved", "released"):
        return business_rule_error("Production order must be approved or released to start")
    po.status = "started"
    po.save(update_fields=["status"])
    return success_response(data=ProductionOrderSerializer(po).data, message="Production started")


@api_view(["POST"])
def production_order_complete(request, pk):
    """Complete production — sets status to completed."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    try:
        po = ProductionOrder.objects.get(pk=pk, company=request.user.company)
    except ProductionOrder.DoesNotExist:
        return not_found_response("Production order not found")
    if po.status != "started":
        return business_rule_error("Production order must be started to complete")
    po.status = "completed"
    po.save(update_fields=["status"])
    return success_response(data=ProductionOrderSerializer(po).data, message="Production completed")


# ─── Material Consumption ─────────────────────────────────────

@api_view(["GET", "POST"])
def material_consumption_list(request):
    """List or create material consumption records."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    company = request.user.company
    if request.method == "GET":
        qs = MaterialConsumption.objects.filter(company=company)
        po_id = request.query_params.get("production_order")
        if po_id:
            qs = qs.filter(production_order_id=po_id)
        return success_response(data=MaterialConsumptionSerializer(qs, many=True).data)
    elif request.method == "POST":
        data = request.data.copy()
        serializer = MaterialConsumptionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        mc = serializer.save(company=company, consumed_by=request.user)
        return success_response(
            data=MaterialConsumptionSerializer(mc).data,
            message="Material consumption recorded",
            http_status_code=status.HTTP_201_CREATED,
        )


# ─── Finished Goods Receipt ───────────────────────────────────

@api_view(["GET", "POST"])
def finished_goods_receipt_list(request):
    """List or create finished goods receipts."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    company = request.user.company
    if request.method == "GET":
        qs = FinishedGoodsReceipt.objects.filter(company=company)
        return success_response(data=FinishedGoodsReceiptSerializer(qs, many=True).data)
    elif request.method == "POST":
        data = request.data.copy()
        serializer = FinishedGoodsReceiptSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        fgr = serializer.save(company=company, received_by=request.user)
        return success_response(
            data=FinishedGoodsReceiptSerializer(fgr).data,
            message="Finished goods receipt recorded",
            http_status_code=status.HTTP_201_CREATED,
        )


# ─── Manufacturing Summary ────────────────────────────────────

@api_view(["GET"])
def manufacturing_summary(request):
    """Return manufacturing dashboard summary."""
    gate = _check_manufacturing_module(request)
    if gate:
        return gate
    company = request.user.company
    active_pos = ProductionOrder.objects.filter(
        company=company, status__in=("started", "released")
    ).count()
    draft_pos = ProductionOrder.objects.filter(company=company, status="draft").count()
    completed_pos = ProductionOrder.objects.filter(company=company, status="completed").count()
    active_boms = BOM.objects.filter(company=company, status="active").count()
    work_centers = WorkCenter.objects.filter(company=company, is_active=True).count()
    return success_response(data={
        "active_production_orders": active_pos,
        "draft_production_orders": draft_pos,
        "completed_production_orders": completed_pos,
        "active_boms": active_boms,
        "active_work_centers": work_centers,
    })
