"""
Manufacturing Cost Engine — per MANUFACTURING_MODULE.md §15-§17.

Supports:
- Standard Cost, Actual Cost, FIFO Cost methods
- Direct Material Cost, Direct Labor Cost, Machine Cost, Overhead Cost
- Production Variance calculation (Material, Labor, Overhead, Efficiency)
- WIP (Work In Progress) valuation
- Scrap cost allocation
"""

import logging
from decimal import Decimal
from typing import Dict, Optional

from django.db import transaction
from django.db.models import Sum

from apps.finance.exceptions import ValidationError
from .models import (
    ProductionOrder, MaterialConsumption, FinishedGoodsReceipt,
    BOM, BOMLine,
)

logger = logging.getLogger(__name__)


class CostMethod:
    STANDARD = "standard"
    ACTUAL = "actual"
    FIFO = "fifo"
    AVERAGE = "average"


class ManufacturingCostEngine:
    """
    Central cost calculation engine for manufacturing.
    Per MANUFACTURING_MODULE.md §15: Manufacturing Cost Engine.
    Per MANUFACTURING_MODULE.md §16: Cost Methods.
    Per MANUFACTURING_MODULE.md §17: Production Variance.
    """

    @staticmethod
    @transaction.atomic
    def calculate_material_cost(production_order: ProductionOrder) -> Decimal:
        """
        Calculate total material cost from MaterialConsumption records.
        Per MANUFACTURING_MODULE.md §15: Direct Material Cost = Σ(quantity × unit_cost).
        """
        total = MaterialConsumption.objects.filter(
            production_order=production_order
        ).aggregate(
            total=Sum("total_cost")
        )["total"] or Decimal("0")

        production_order.material_cost = total
        production_order.save(update_fields=["material_cost"])

        logger.info(f"Material cost for {production_order.number}: {total} Rial")
        return total

    @staticmethod
    def calculate_labor_cost(
        production_order: ProductionOrder,
        labor_hours: Decimal,
        hourly_rate: Decimal,
    ) -> Decimal:
        """
        Calculate direct labor cost.
        Per MANUFACTURING_MODULE.md §15: Direct Labor Cost = Labor Hours × Labor Rate.
        """
        total = labor_hours * hourly_rate
        production_order.labor_cost = total
        production_order.save(update_fields=["labor_cost"])

        logger.info(f"Labor cost for {production_order.number}: {total} Rial")
        return total

    @staticmethod
    def calculate_machine_cost(
        production_order: ProductionOrder,
        machine_hours: Decimal,
        hourly_rate: Decimal,
    ) -> Decimal:
        """
        Calculate machine operating cost.
        Per MANUFACTURING_MODULE.md §15: Machine Cost = Machine Hours × Machine Rate.
        """
        total = machine_hours * hourly_rate
        production_order.machine_cost = total
        production_order.save(update_fields=["machine_cost"])

        logger.info(f"Machine cost for {production_order.number}: {total} Rial")
        return total

    @staticmethod
    def calculate_overhead_cost(
        production_order: ProductionOrder,
        overhead_amount: Decimal,
    ) -> Decimal:
        """
        Allocate overhead costs (electricity, rent, depreciation, etc.).
        Per MANUFACTURING_MODULE.md §15: Overhead Cost.
        """
        production_order.overhead_cost = overhead_amount
        production_order.save(update_fields=["overhead_cost"])

        logger.info(f"Overhead cost for {production_order.number}: {overhead_amount} Rial")
        return overhead_amount

    @staticmethod
    def calculate_total_cost(production_order: ProductionOrder) -> Decimal:
        """
        Recalculate total cost from all cost components.
        Per MANUFACTURING_MODULE.md §15: Total Cost = Material + Labor + Machine + Overhead.
        """
        ManufacturingCostEngine.calculate_material_cost(production_order)
        production_order.total_cost = (
            production_order.material_cost
            + production_order.labor_cost
            + production_order.machine_cost
            + production_order.overhead_cost
        )
        production_order.save(update_fields=["total_cost"])

        logger.info(f"Total cost for {production_order.number}: {production_order.total_cost} Rial")
        return production_order.total_cost

    @staticmethod
    def calculate_unit_cost(production_order: ProductionOrder) -> Decimal:
        """Calculate cost per unit produced."""
        if production_order.quantity <= 0:
            return Decimal("0")
        return production_order.total_cost / production_order.quantity

    @staticmethod
    def calculate_unit_cost_from_receipt(receipt: FinishedGoodsReceipt) -> Decimal:
        """Calculate unit cost from a finished goods receipt."""
        if receipt.quantity_received <= 0:
            return Decimal("0")
        return receipt.total_cost / receipt.quantity_received


class VarianceEngine:
    """
    Production variance analysis.
    Per MANUFACTURING_MODULE.md §17: Production Variance.
    Formula: Actual Cost - Standard Cost = Production Variance.
    """

    @staticmethod
    def calculate_material_variance(
        actual_material_cost: Decimal,
        standard_material_cost: Decimal,
    ) -> Dict:
        """
        Material Variance = Actual Material Cost - Standard Material Cost.
        """
        variance = actual_material_cost - standard_material_cost
        return {
            "type": "material",
            "actual": actual_material_cost,
            "standard": standard_material_cost,
            "variance": variance,
            "is_favorable": variance <= 0,
        }

    @staticmethod
    def calculate_labor_variance(
        actual_labor_cost: Decimal,
        standard_labor_cost: Decimal,
    ) -> Dict:
        """
        Labor Variance = Actual Labor Cost - Standard Labor Cost.
        """
        variance = actual_labor_cost - standard_labor_cost
        return {
            "type": "labor",
            "actual": actual_labor_cost,
            "standard": standard_labor_cost,
            "variance": variance,
            "is_favorable": variance <= 0,
        }

    @staticmethod
    def calculate_overhead_variance(
        actual_overhead: Decimal,
        standard_overhead: Decimal,
    ) -> Dict:
        """
        Overhead Variance = Actual Overhead - Standard Overhead.
        """
        variance = actual_overhead - standard_overhead
        return {
            "type": "overhead",
            "actual": actual_overhead,
            "standard": standard_overhead,
            "variance": variance,
            "is_favorable": variance <= 0,
        }

    @staticmethod
    def calculate_efficiency_variance(
        actual_quantity: Decimal,
        standard_quantity: Decimal,
        standard_cost_per_unit: Decimal,
    ) -> Dict:
        """
        Efficiency Variance = (Actual Qty - Standard Qty) × Standard Cost/Unit.
        """
        variance = (actual_quantity - standard_quantity) * standard_cost_per_unit
        return {
            "type": "efficiency",
            "actual_quantity": actual_quantity,
            "standard_quantity": standard_quantity,
            "variance": variance,
            "is_favorable": variance <= 0,
        }

    @staticmethod
    def calculate_total_variance(production_order: ProductionOrder) -> Dict:
        """
        Calculate total production variance against standard costs from BOM.
        Per MANUFACTURING_MODULE.md §17: Actual Cost - Standard Cost = Production Variance.
        """
        actual_total = production_order.total_cost

        # Calculate standard cost from BOM
        standard_total = Decimal("0")
        if production_order.bom:
            bom_lines = production_order.bom.lines.all()
            for line in bom_lines:
                standard_total += line.quantity * line.unit_cost * production_order.quantity
        else:
            # No BOM — standard cost equals actual (no variance possible)
            standard_total = actual_total

        variance = actual_total - standard_total

        return {
            "production_order": production_order.number,
            "actual_cost": actual_total,
            "standard_cost": standard_total,
            "total_variance": variance,
            "is_favorable": variance <= 0,
            "variance_percentage": (
                (variance / standard_total * Decimal("100"))
                if standard_total > 0 else Decimal("0")
            ),
        }


class WIPEngine:
    """
    Work In Progress valuation.
    Per MANUFACTURING_MODULE.md §18: WIP Value.
    WIP = Material Consumed + Labor Cost + Machine Cost + Overhead Allocation.
    """

    @staticmethod
    def calculate_wip_value(production_order: ProductionOrder) -> Decimal:
        """Calculate current WIP value for a production order."""
        wip = (
            production_order.material_cost
            + production_order.labor_cost
            + production_order.machine_cost
            + production_order.overhead_cost
        )
        logger.info(f"WIP value for {production_order.number}: {wip} Rial")
        return wip

    @staticmethod
    def get_all_wip(company) -> Dict:
        """Get total WIP across all in-progress production orders."""
        active_orders = ProductionOrder.objects.filter(
            company=company,
            status__in=("started", "released", "approved"),
        )

        total_wip = Decimal("0")
        orders = []
        for po in active_orders:
            wip = WIPEngine.calculate_wip_value(po)
            total_wip += wip
            orders.append({
                "number": po.number,
                "product_name": po.product_name,
                "wip_value": wip,
            })

        return {
            "total_wip": total_wip,
            "order_count": len(orders),
            "orders": orders,
        }


class ScrapEngine:
    """
    Scrap management and cost allocation.
    Per MANUFACTURING_MODULE.md §19: Scrap Management.
    """

    @staticmethod
    def calculate_scrap_cost(
        quantity_scrap: Decimal,
        unit_cost: Decimal,
        scrap_type: str = "normal",
    ) -> Dict:
        """
        Calculate scrap cost allocation.
        Per MANUFACTURING_MODULE.md §19: Scrap Cost Allocation.
        """
        total_scrap_cost = quantity_scrap * unit_cost
        return {
            "quantity_scrap": quantity_scrap,
            "unit_cost": unit_cost,
            "total_scrap_cost": total_scrap_cost,
            "scrap_type": scrap_type,
            # Accounting: Debit Scrap Loss, Credit Production WIP
            "accounting_entry": {
                "debit_account": "scrap_loss",
                "credit_account": "production_wip",
                "amount": total_scrap_cost,
            },
        }

    @staticmethod
    def calculate_scrap_percentage(
        quantity_produced: Decimal,
        quantity_rejected: Decimal,
    ) -> Decimal:
        """Calculate scrap percentage from production output."""
        if quantity_produced <= 0:
            return Decimal("0")
        return (quantity_rejected / quantity_produced) * Decimal("100")


class ByProductEngine:
    """
    By-product management and cost allocation.
    Per MANUFACTURING_MODULE.md §20: By Product Management.
    """

    @staticmethod
    def allocate_cost(
        main_product_cost: Decimal,
        by_products: list,
        method: str = "market_value",
    ) -> list:
        """
        Allocate cost across main product and by-products.
        Per MANUFACTURING_MODULE.md §20: Cost allocation methods.
        - Quantity Based
        - Market Value Based
        """
        if not by_products:
            return [{"product": "main", "allocated_cost": main_product_cost}]

        total_byproduct_value = sum(bp.get("market_value", Decimal("0")) for bp in by_products)
        total_value = main_product_cost + total_byproduct_value

        allocations = []
        for bp in by_products:
            if method == "market_value" and total_value > 0:
                bp_cost = (bp["market_value"] / total_value) * main_product_cost
            else:
                # Quantity-based: divide equally
                bp_cost = main_product_cost / (len(by_products) + 1)

            allocations.append({
                "product": bp.get("name", "by-product"),
                "allocated_cost": bp_cost,
            })

        # Main product gets the remainder
        main_allocated = main_product_cost - sum(a["allocated_cost"] for a in allocations)
        allocations.insert(0, {"product": "main", "allocated_cost": main_allocated})

        return allocations
