"""
Manufacturing Module Models — Enterprise ERP Production Lifecycle.

Per MANUFACTURING_MODULE.md:
- §4: Bill of Material (BOM) — structure of manufactured products
- §5: Routing Management — production operations
- §6: Work Center Management — production resources
- §11: Production Order — main manufacturing transaction
- §13: Material Consumption — inventory transactions
- §14: Finished Goods Receipt — post-production inventory
- §15: Manufacturing Cost Engine — direct material, labor, machine, overhead

Supports: Discrete, Assembly, Process, Batch, MTS, MTO, ETO production models.
"""

from decimal import Decimal
from django.db import models
from django.conf import settings


# ─── BOM (Bill of Material) ────────────────────────────────────

class BOM(models.Model):
    """
    Bill of Material header.
    Per MANUFACTURING_MODULE.md §4.1: BOM Header.
    """
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("obsolete", "Obsolete"),
    ]

    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="boms")
    number = models.CharField(max_length=50, help_text="BOM Number")
    product_name = models.CharField(max_length=200, help_text="Product to be manufactured")
    product_code = models.CharField(max_length=50, blank=True, default="")
    version = models.IntegerField(default=1, help_text="BOM version number")
    revision = models.CharField(max_length=20, blank=True, default="", help_text="Engineering revision")
    effective_date = models.DateField(help_text="Date from which this BOM is effective")
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    description = models.TextField(blank=True, default="")
    base_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("1.00"),
                                         help_text="Base quantity for this BOM")
    unit = models.CharField(max_length=20, default="عدد", help_text="Unit of measure")
    # Approval workflow
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name="approved_boms")
    approved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name="created_boms")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("company", "number", "version")]
        ordering = ["-version", "number"]

    def __str__(self):
        return f"{self.number} v{self.version} — {self.product_name}"

    @property
    def total_cost(self):
        """Sum of (quantity × unit_cost) for all BOM lines."""
        return sum(
            (line.quantity * line.unit_cost for line in self.lines.all()),
            Decimal("0"),
        )


class BOMLine(models.Model):
    """
    BOM line item — component of a manufactured product.
    Per MANUFACTURING_MODULE.md §4.2: BOM Lines.
    """
    CONSUMPTION_TYPES = [
        ("manual", "Manual Issue"),
        ("backflush", "Backflush"),
        ("automatic", "Automatic Consumption"),
    ]

    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name="lines")
    line_number = models.IntegerField(help_text="Sequence number")
    component_name = models.CharField(max_length=200, help_text="Component material name")
    component_code = models.CharField(max_length=50, blank=True, default="")
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal("1.0000"),
                                    help_text="Quantity required")
    unit = models.CharField(max_length=20, default="عدد")
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"),
                                     help_text="Standard cost per unit (Rial)")
    scrap_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"),
                                            help_text="Expected scrap %")
    consumption_type = models.CharField(max_length=20, choices=CONSUMPTION_TYPES, default="manual")
    substitute_component = models.CharField(max_length=200, blank=True, default="",
                                             help_text="Substitute material if any")
    notes = models.CharField(max_length=500, blank=True, default="")
    # Link to accounting
    kol = models.ForeignKey("finance.KolAccount", on_delete=models.SET_NULL,
                             null=True, blank=True, help_text="Accounting Kol for this component")

    class Meta:
        ordering = ["line_number"]
        unique_together = [("bom", "line_number")]

    def __str__(self):
        return f"L{self.line_number}: {self.component_name} × {self.quantity}"

    @property
    def extended_cost(self):
        return self.quantity * self.unit_cost


# ─── Routing (Production Operations) ───────────────────────────

class Routing(models.Model):
    """
    Routing header — defines the sequence of operations.
    Per MANUFACTURING_MODULE.md §5: Routing Management.
    """
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("obsolete", "Obsolete"),
    ]

    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="routings")
    number = models.CharField(max_length=50, help_text="Routing Number")
    name = models.CharField(max_length=200, help_text="Routing name")
    product_name = models.CharField(max_length=200, blank=True, default="")
    version = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    description = models.TextField(blank=True, default="")
    # Estimated totals
    estimated_hours = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"),
                                           help_text="Total estimated production hours")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name="created_routings")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("company", "number", "version")]
        ordering = ["number"]

    def __str__(self):
        return f"{self.number} — {self.name}"


class RoutingOperation(models.Model):
    """
    Single operation in a routing.
    Per MANUFACTURING_MODULE.md §5: Each operation contains operation code, name,
    sequence, work center, required time, labor/machine requirements.
    """
    routing = models.ForeignKey(Routing, on_delete=models.CASCADE, related_name="operations")
    sequence = models.IntegerField(help_text="Operation sequence number")
    code = models.CharField(max_length=20, help_text="Operation code (e.g. CUT, ASM)")
    name = models.CharField(max_length=200, help_text="Operation name")
    description = models.TextField(blank=True, default="")
    # Work center
    work_center = models.ForeignKey("WorkCenter", on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name="operations")
    # Time requirements
    setup_time_minutes = models.IntegerField(default=0, help_text="Setup time in minutes")
    run_time_minutes = models.IntegerField(default=0, help_text="Run time per unit in minutes")
    labor_hours = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"),
                                       help_text="Required labor hours")
    machine_hours = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"),
                                         help_text="Required machine hours")
    # Quality
    is_quality_checkpoint = models.BooleanField(default=False,
                                                 help_text="Quality inspection at this step?")
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["sequence"]
        unique_together = [("routing", "sequence")]

    def __str__(self):
        return f"{self.code} — {self.name}"


# ─── Work Center ───────────────────────────────────────────────

class WorkCenter(models.Model):
    """
    Work center — production resource.
    Per MANUFACTURING_MODULE.md §6: Work Center Management.
    """
    TYPE_CHOICES = [
        ("machine", "Machine"),
        ("production_line", "Production Line"),
        ("department", "Department"),
        ("external_vendor", "External Vendor"),
    ]

    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="work_centers")
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    work_center_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="machine")
    capacity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"),
                                    help_text="Units per hour")
    efficiency = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("100.00"),
                                      help_text="Efficiency %")
    hourly_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"),
                                       help_text="Hourly operating cost (Rial)")
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("company", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


# ─── Production Order ──────────────────────────────────────────

class ProductionOrder(models.Model):
    """
    Production Order — main manufacturing transaction.
    Per MANUFACTURING_MODULE.md §11: Production Order.
    """
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("released", "Released"),
        ("started", "Started"),
        ("paused", "Paused"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    PRIORITY_CHOICES = [
        (1, "Low"),
        (2, "Normal"),
        (3, "High"),
        (4, "Urgent"),
    ]

    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="production_orders")
    number = models.CharField(max_length=50, help_text="Production Order number")
    # Product
    product_name = models.CharField(max_length=200, help_text="Product to manufacture")
    product_code = models.CharField(max_length=50, blank=True, default="")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("1.00"),
                                    help_text="Quantity to produce")
    unit = models.CharField(max_length=20, default="عدد")
    # BOM & Routing
    bom = models.ForeignKey(BOM, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name="production_orders")
    routing = models.ForeignKey(Routing, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="production_orders")
    # Dates
    start_date_jalali = models.CharField(max_length=10, blank=True, default="")
    end_date_jalali = models.CharField(max_length=10, blank=True, default="")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    # Costs
    material_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    labor_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    machine_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    overhead_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    # Accounting
    journal_voucher = models.ForeignKey("finance.JournalVoucher", on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name="production_orders")
    # Approval
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name="approved_production_orders")
    approved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name="created_production_orders")
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("company", "number")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.number} — {self.product_name} × {self.quantity}"

    def calculate_total_cost(self):
        self.total_cost = self.material_cost + self.labor_cost + self.machine_cost + self.overhead_cost
        self.save(update_fields=["total_cost"])


# ─── Material Consumption ──────────────────────────────────────

class MaterialConsumption(models.Model):
    """
    Records material consumed during production.
    Per MANUFACTURING_MODULE.md §13: Material Consumption.
    Accounting: Debit Production WIP, Credit Raw Material Inventory.
    """
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="material_consumptions")
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE,
                                          related_name="material_consumptions")
    component_name = models.CharField(max_length=200)
    component_code = models.CharField(max_length=50, blank=True, default="")
    quantity_consumed = models.DecimalField(max_digits=12, decimal_places=4)
    unit = models.CharField(max_length=20, default="عدد")
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    # Link to BOM line
    bom_line = models.ForeignKey(BOMLine, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="consumptions")
    # Accounting
    journal_voucher = models.ForeignKey("finance.JournalVoucher", on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name="material_consumptions")
    consumed_at = models.DateTimeField(auto_now_add=True)
    consumed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name="material_consumptions")
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["-consumed_at"]

    def __str__(self):
        return f"{self.component_name} × {self.quantity_consumed} for {self.production_order.number}"

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity_consumed * self.unit_cost
        super().save(*args, **kwargs)


# ─── Finished Goods Receipt ────────────────────────────────────

class FinishedGoodsReceipt(models.Model):
    """
    Records finished goods received after production completion.
    Per MANUFACTURING_MODULE.md §14: Finished Goods Receipt.
    Accounting: Debit Finished Goods Inventory, Credit Production WIP.
    """
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="finished_goods_receipts")
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE,
                                          related_name="finished_goods_receipts")
    product_name = models.CharField(max_length=200)
    quantity_received = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=20, default="عدد")
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    quantity_rejected = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"),
                                             help_text="Quantity rejected in QC")
    # Accounting
    journal_voucher = models.ForeignKey("finance.JournalVoucher", on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name="finished_goods_receipts")
    received_at = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name="finished_goods_receipts")
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.product_name} × {self.quantity_received} — {self.production_order.number}"

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity_received * self.unit_cost
        super().save(*args, **kwargs)
