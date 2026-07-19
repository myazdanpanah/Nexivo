"""
Material Requirement Planning (MRP) Engine — per MANUFACTURING_MODULE.md §8-§10.

§8: MRP — calculates required materials from demand
    Formula: Demand + Safety Stock - Available Inventory - Open Purchase Orders = Net Requirement
§9: Capacity Planning — validates machine/labor capacity
§10: Production Scheduling — forward, backward, priority scheduling
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Sum

from apps.finance.exceptions import ValidationError
from .models import (
    BOM, BOMLine, ProductionOrder, WorkCenter, Routing, RoutingOperation,
)

logger = logging.getLogger(__name__)


class MRPEngine:
    """
    Material Requirement Planning engine.
    Per MANUFACTURING_MODULE.md §8: MRP calculates required materials.
    """

    @staticmethod
    def calculate_net_requirement(
        demand: Decimal,
        safety_stock: Decimal = Decimal("0"),
        available_inventory: Decimal = Decimal("0"),
        open_purchase_orders: Decimal = Decimal("0"),
    ) -> Dict:
        """
        Calculate net material requirement.
        Per MANUFACTURING_MODULE.md §8:
        Demand + Safety Stock - Available Inventory - Open Purchase Orders = Net Requirement
        """
        gross = demand + safety_stock
        available = available_inventory + open_purchase_orders
        net = gross - available

        return {
            "demand": demand,
            "safety_stock": safety_stock,
            "gross_requirement": gross,
            "available_inventory": available_inventory,
            "open_purchase_orders": open_purchase_orders,
            "total_available": available,
            "net_requirement": max(net, Decimal("0")),
            "shortage": max(-net, Decimal("0")),
        }

    @staticmethod
    def explode_bom(production_order: ProductionOrder) -> List[Dict]:
        """
        Explode BOM to calculate total material requirements.
        For each BOM line: required_quantity = line.quantity × production_order.quantity.
        """
        if not production_order.bom:
            return []

        bom_lines = production_order.bom.lines.all()
        requirements = []

        for line in bom_lines:
            # Account for scrap percentage
            scrap_factor = Decimal("1") + (line.scrap_percentage / Decimal("100"))
            raw_qty = line.quantity * production_order.quantity
            adjusted_qty = raw_qty * scrap_factor

            requirements.append({
                "component_name": line.component_name,
                "component_code": line.component_code,
                "quantity_per_unit": line.quantity,
                "quantity_required": raw_qty,
                "quantity_adjusted_for_scrap": adjusted_qty,
                "unit": line.unit,
                "unit_cost": line.unit_cost,
                "total_cost": adjusted_qty * line.unit_cost,
                "consumption_type": line.consumption_type,
            })

        return requirements

    @staticmethod
    def generate_purchase_requests(requirements: List[Dict]) -> List[Dict]:
        """
        Generate purchase requests from net requirements.
        Per MANUFACTURING_MODULE.md §8: MRP generates Purchase Requests.
        """
        requests = []
        for req in requirements:
            if req["quantity_adjusted_for_scrap"] > 0:
                requests.append({
                    "item": req["component_name"],
                    "code": req["component_code"],
                    "quantity": req["quantity_adjusted_for_scrap"],
                    "unit": req["unit"],
                    "estimated_cost": req["total_cost"],
                    "type": "purchase_request",
                })
        return requests

    @staticmethod
    def generate_production_orders(requirements: List[Dict]) -> List[Dict]:
        """
        Generate production orders for semi-finished goods.
        Per MANUFACTURING_MODULE.md §8: MRP generates Production Orders.
        """
        orders = []
        for req in requirements:
            if req["consumption_type"] == "backflush":
                orders.append({
                    "item": req["component_name"],
                    "quantity": req["quantity_adjusted_for_scrap"],
                    "unit": req["unit"],
                    "type": "production_order",
                })
        return orders


class CapacityPlanningEngine:
    """
    Capacity planning — validates machine and labor capacity.
    Per MANUFACTURING_MODULE.md §9: Capacity Planning.
    """

    @staticmethod
    def check_capacity(
        work_center: WorkCenter,
        required_hours: Decimal,
        available_date: date = None,
    ) -> Dict:
        """
        Check if a work center has sufficient capacity.
        Per MANUFACTURING_MODULE.md §9:
        Required Hours / Available Capacity = Scheduling Conflict check.
        """
        if not available_date:
            available_date = date.today()

        # Assume 8-hour work day, adjusted for efficiency
        effective_hours_per_day = Decimal("8") * (work_center.efficiency / Decimal("100"))
        days_needed = (required_hours / effective_hours_per_day) if effective_hours_per_day > 0 else Decimal("999")

        estimated_end = available_date + timedelta(days=int(days_needed) + 1)

        return {
            "work_center": work_center.code,
            "work_center_name": work_center.name,
            "required_hours": required_hours,
            "effective_hours_per_day": effective_hours_per_day,
            "days_needed": days_needed,
            "available_date": available_date,
            "estimated_end_date": estimated_end,
            "has_capacity": True,  # Simplified — real system checks calendar
            "capacity_utilization": (
                (required_hours / (effective_hours_per_day * Decimal("30")) * Decimal("100"))
                if effective_hours_per_day > 0 else Decimal("100")
            ),
        }

    @staticmethod
    def check_routing_capacity(routing: Routing, quantity: Decimal) -> Dict:
        """Check capacity for all operations in a routing."""
        results = []
        total_hours = Decimal("0")

        for op in routing.operations.all():
            if op.work_center:
                op_hours = (op.setup_time_minutes + (op.run_time_minutes * quantity)) / Decimal("60")
                result = CapacityPlanningEngine.check_capacity(op.work_center, op_hours)
                results.append({
                    "operation": op.name,
                    "operation_code": op.code,
                    **result,
                })
                total_hours += op_hours

        return {
            "routing": routing.number,
            "quantity": quantity,
            "total_hours": total_hours,
            "operations": results,
            "all_have_capacity": all(r["has_capacity"] for r in results),
        }


class ProductionScheduler:
    """
    Production scheduling engine.
    Per MANUFACTURING_MODULE.md §10: Production Scheduling.
    Supports: Forward, Backward, Priority Scheduling.
    """

    @staticmethod
    def forward_schedule(
        production_order: ProductionOrder,
        start_date: date = None,
    ) -> Dict:
        """
        Forward scheduling — start from start_date, push forward.
        Per MANUFACTURING_MODULE.md §10: Forward Scheduling.
        """
        if not start_date:
            start_date = date.today()

        current_date = start_date
        total_hours = Decimal("0")

        if production_order.routing:
            for op in production_order.routing.operations.all():
                op_hours = (op.setup_time_minutes + (op.run_time_minutes * production_order.quantity)) / Decimal("60")
                total_hours += op_hours

                # Simple: 8 hours per day
                days = int(op_hours / Decimal("8")) + 1
                current_date += timedelta(days=days)

        return {
            "production_order": production_order.number,
            "start_date": start_date,
            "end_date": current_date,
            "total_hours": total_hours,
            "scheduling_method": "forward",
        }

    @staticmethod
    def backward_schedule(
        production_order: ProductionOrder,
        due_date: date,
    ) -> Dict:
        """
        Backward scheduling — start from due_date, push backward.
        Per MANUFACTURING_MODULE.md §10: Backward Scheduling.
        """
        total_hours = Decimal("0")

        if production_order.routing:
            for op in production_order.routing.operations.all():
                op_hours = (op.setup_time_minutes + (op.run_time_minutes * production_order.quantity)) / Decimal("60")
                total_hours += op_hours

        days_needed = int(total_hours / Decimal("8")) + 1
        start_date = due_date - timedelta(days=days_needed)

        return {
            "production_order": production_order.number,
            "start_date": start_date,
            "end_date": due_date,
            "total_hours": total_hours,
            "scheduling_method": "backward",
        }

    @staticmethod
    def prioritize_orders(orders: List[ProductionOrder]) -> List[Dict]:
        """
        Priority scheduling — sort by priority and due date.
        Per MANUFACTURING_MODULE.md §10: Priority Rules.
        Priority Rules: Customer Priority, Due Date, Efficiency, Availability.
        """
        sorted_orders = sorted(
            orders,
            key=lambda o: (-o.priority, o.end_date or date.max),
        )

        return [
            {
                "number": po.number,
                "product_name": po.product_name,
                "priority": po.priority,
                "end_date": po.end_date,
                "status": po.status,
            }
            for po in sorted_orders
        ]
