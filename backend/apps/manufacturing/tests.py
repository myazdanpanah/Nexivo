"""
Manufacturing Module Tests — per MANUFACTURING_MODULE.md §29: Completion Criteria.
"""

import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.tests_helpers import create_test_company, create_test_user
from apps.finance.models import FiscalYear, AccountGroup, KolAccount
from .models import (
    BOM, BOMLine, Routing, RoutingOperation, WorkCenter,
    ProductionOrder, MaterialConsumption, FinishedGoodsReceipt,
)

User = get_user_model()


class ManufacturingTestBase(TestCase):
    """Shared setUp for manufacturing tests."""

    def setUp(self):
        self.company = create_test_company(name="ManufTestCo")
        self.user = create_test_user(username="manufuser", company=self.company, role="ceo")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        # Enable the manufacturing module for the company
        self.company.enable_module("manufacturing")
        # Fiscal year (for accounting links)
        self.fy = FiscalYear.objects.create(
            company=self.company, name="1404",
            start_date_jalali="1403/01/01", end_date_jalali="1404/01/01",
            start_date=datetime.date(2024, 3, 20),
            end_date=datetime.date(2025, 3, 19),
        )


class BOMTests(ManufacturingTestBase):
    """Tests for BOM CRUD and approval."""

    def test_create_bom(self):
        resp = self.client.post("/api/v1/manufacturing/boms/", {
            "number": "BOM-001",
            "product_name": "Laptop Assembly",
            "product_code": "LAP-001",
            "version": 1,
            "effective_date": "2025-06-21",
            "status": "draft",
            "base_quantity": "1.00",
            "unit": "عدد",
        }, format="json")
        self.assertIn(resp.status_code, [200, 201])
        data = resp.data.get("data", resp.data)
        self.assertEqual(data["number"], "BOM-001")
        self.assertEqual(data["product_name"], "Laptop Assembly")

    def test_list_boms(self):
        BOM.objects.create(
            company=self.company, number="BOM-100",
            product_name="Widget", effective_date=datetime.date(2025, 1, 1),
        )
        resp = self.client.get("/api/v1/manufacturing/boms/")
        self.assertEqual(resp.status_code, 200)

    def test_bom_approve(self):
        bom = BOM.objects.create(
            company=self.company, number="BOM-200",
            product_name="Widget", effective_date=datetime.date(2025, 1, 1),
            status="draft",
        )
        resp = self.client.post(f"/api/v1/manufacturing/boms/{bom.id}/approve/")
        self.assertEqual(resp.status_code, 200)
        bom.refresh_from_db()
        self.assertEqual(bom.status, "active")
        self.assertEqual(bom.approved_by, self.user)

    def test_bom_approve_non_draft_fails(self):
        bom = BOM.objects.create(
            company=self.company, number="BOM-300",
            product_name="Widget", effective_date=datetime.date(2025, 1, 1),
            status="active",
        )
        resp = self.client.post(f"/api/v1/manufacturing/boms/{bom.id}/approve/")
        self.assertEqual(resp.status_code, 422)


class RoutingTests(ManufacturingTestBase):
    """Tests for Routing CRUD."""

    def test_create_routing(self):
        resp = self.client.post("/api/v1/manufacturing/routings/", {
            "number": "RT-001",
            "name": "Assembly Routing",
            "version": 1,
            "status": "draft",
        }, format="json")
        self.assertIn(resp.status_code, [200, 201])

    def test_routing_with_operations(self):
        wc = WorkCenter.objects.create(
            company=self.company, code="WC-1", name="Assembly Line",
            work_center_type="production_line",
        )
        resp = self.client.post("/api/v1/manufacturing/routings/", {
            "number": "RT-002",
            "name": "Cut & Assemble",
            "version": 1,
            "operations": [
                {"sequence": 10, "code": "CUT", "name": "Cutting", "work_center": wc.id, "run_time_minutes": 15},
                {"sequence": 20, "code": "ASM", "name": "Assembly", "work_center": wc.id, "run_time_minutes": 30},
            ],
        }, format="json")
        self.assertIn(resp.status_code, [200, 201])
        routing = Routing.objects.get(number="RT-002")
        self.assertEqual(routing.operations.count(), 2)


class WorkCenterTests(ManufacturingTestBase):
    """Tests for Work Center CRUD."""

    def test_create_work_center(self):
        resp = self.client.post("/api/v1/manufacturing/work-centers/", {
            "code": "CNC-01",
            "name": "CNC Machine 1",
            "work_center_type": "machine",
            "capacity": "10.00",
            "efficiency": "95.00",
            "hourly_cost": "500000.00",
        }, format="json")
        self.assertIn(resp.status_code, [200, 201])
        data = resp.data.get("data", resp.data)
        self.assertEqual(data["code"], "CNC-01")

    def test_list_work_centers(self):
        WorkCenter.objects.create(company=self.company, code="WC-A", name="Line A")
        resp = self.client.get("/api/v1/manufacturing/work-centers/")
        self.assertEqual(resp.status_code, 200)


class ProductionOrderTests(ManufacturingTestBase):
    """Tests for Production Order CRUD and workflow."""

    def _create_po(self, status="draft"):
        return ProductionOrder.objects.create(
            company=self.company, number="PO-001",
            product_name="Widget", quantity=Decimal("100"),
            status=status,
        )

    def test_create_production_order(self):
        resp = self.client.post("/api/v1/manufacturing/production-orders/", {
            "number": "PO-NEW",
            "product_name": "Widget",
            "quantity": "100.00",
        }, format="json")
        self.assertIn(resp.status_code, [200, 201])

    def test_approve_production_order(self):
        po = self._create_po(status="draft")
        resp = self.client.post(f"/api/v1/manufacturing/production-orders/{po.id}/approve/")
        self.assertEqual(resp.status_code, 200)
        po.refresh_from_db()
        self.assertEqual(po.status, "approved")

    def test_approve_non_draft_fails(self):
        po = self._create_po(status="approved")
        resp = self.client.post(f"/api/v1/manufacturing/production-orders/{po.id}/approve/")
        self.assertEqual(resp.status_code, 422)

    def test_start_production_order(self):
        po = self._create_po(status="approved")
        resp = self.client.post(f"/api/v1/manufacturing/production-orders/{po.id}/start/")
        self.assertEqual(resp.status_code, 200)
        po.refresh_from_db()
        self.assertEqual(po.status, "started")

    def test_complete_production_order(self):
        po = self._create_po(status="started")
        resp = self.client.post(f"/api/v1/manufacturing/production-orders/{po.id}/complete/")
        self.assertEqual(resp.status_code, 200)
        po.refresh_from_db()
        self.assertEqual(po.status, "completed")

    def test_cannot_complete_draft(self):
        po = self._create_po(status="draft")
        resp = self.client.post(f"/api/v1/manufacturing/production-orders/{po.id}/complete/")
        self.assertEqual(resp.status_code, 422)


class MaterialConsumptionTests(ManufacturingTestBase):
    """Tests for Material Consumption recording."""

    def test_create_consumption(self):
        po = ProductionOrder.objects.create(
            company=self.company, number="PO-10",
            product_name="Widget", quantity=Decimal("50"), status="started",
        )
        resp = self.client.post("/api/v1/manufacturing/material-consumptions/", {
            "production_order": po.id,
            "component_name": "Steel Sheet",
            "quantity_consumed": "10.0000",
            "unit": "kg",
            "unit_cost": "50000.00",
        }, format="json")
        self.assertIn(resp.status_code, [200, 201])
        data = resp.data.get("data", resp.data)
        self.assertEqual(Decimal(data["total_cost"]), Decimal("500000.00"))


class FinishedGoodsReceiptTests(ManufacturingTestBase):
    """Tests for Finished Goods Receipt."""

    def test_create_receipt(self):
        po = ProductionOrder.objects.create(
            company=self.company, number="PO-20",
            product_name="Widget", quantity=Decimal("50"), status="started",
        )
        resp = self.client.post("/api/v1/manufacturing/finished-goods-receipts/", {
            "production_order": po.id,
            "product_name": "Widget",
            "quantity_received": "48.00",
            "unit": "عدد",
            "unit_cost": "100000.00",
            "quantity_rejected": "2.00",
        }, format="json")
        self.assertIn(resp.status_code, [200, 201])
        data = resp.data.get("data", resp.data)
        self.assertEqual(Decimal(data["total_cost"]), Decimal("4800000.00"))


class ManufacturingSummaryTests(ManufacturingTestBase):
    """Tests for manufacturing summary endpoint."""

    def test_summary_empty(self):
        resp = self.client.get("/api/v1/manufacturing/summary/")
        self.assertEqual(resp.status_code, 200)
        data = resp.data.get("data", resp.data)
        self.assertEqual(data["active_production_orders"], 0)

    def test_summary_with_data(self):
        ProductionOrder.objects.create(
            company=self.company, number="PO-S1", product_name="A",
            quantity=Decimal("10"), status="started",
        )
        WorkCenter.objects.create(company=self.company, code="WC-S", name="Line S")
        BOM.objects.create(
            company=self.company, number="BOM-S1", product_name="A",
            effective_date=datetime.date(2025, 1, 1), status="active",
        )
        resp = self.client.get("/api/v1/manufacturing/summary/")
        self.assertEqual(resp.status_code, 200)
        data = resp.data.get("data", resp.data)
        self.assertEqual(data["active_production_orders"], 1)
        self.assertEqual(data["active_boms"], 1)
        self.assertEqual(data["active_work_centers"], 1)
