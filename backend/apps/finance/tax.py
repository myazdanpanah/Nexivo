"""
Tax Engine — Enterprise ERP Iranian Tax Compliance Layer.

Per TAX_AND_LEGAL_RULES_IRAN.md §1: VAT, Electronic Invoicing, Corporate Tax,
Payroll Tax, Withholding Tax, Tax Reports, Tax Audit Trail.

Per TAX_AND_LEGAL_RULES_IRAN.md §2: Architecture:
    Business Module → Tax Classification → Tax Rule Engine →
    Tax Calculation Engine → Accounting Posting Engine → Tax Reporting Engine

Per TAX_AND_LEGAL_RULES_IRAN.md §4: Tax Master Data — TaxCategory, TaxCode, TaxRule.
Per TAX_AND_LEGAL_RULES_IRAN.md §5: VAT Engine — Output VAT, Input VAT, VAT Payable.
Per TAX_AND_LEGAL_RULES_IRAN.md §20: AI Agent Rules — never hard-code tax rates.

This module defines the foundational models and service.
Full calculator/integration/report modules will be added per §19.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db import transaction, models
from django.conf import settings
from django.db.models import Sum

from .exceptions import ValidationError
from .models import FiscalYear

logger = logging.getLogger(__name__)


# ─── Tax Models ──────────────────────────────────────────────────


class TaxCategory(models.Model):
    """
    Defines tax behavior for items/services.

    Per TAX_AND_LEGAL_RULES_IRAN.md §4.1:
    Examples: TAXABLE, EXEMPT, ZERO_RATE, SPECIAL_RULE
    """
    company = models.ForeignKey(
        "accounts.Company", on_delete=models.CASCADE,
        related_name="tax_categories"
    )
    code = models.CharField(max_length=20, help_text="e.g. TAXABLE, EXEMPT")
    name = models.CharField(max_length=100, help_text="e.g. مشمول مالیات")
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("company", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class TaxCode(models.Model):
    """
    Defines applicable tax and its rate.

    Per TAX_AND_LEGAL_RULES_IRAN.md §4.2:
    Examples: VAT_NORMAL (10%), VAT_EXEMPT (0%), WITHHOLDING_SERVICE (5%)
    """
    company = models.ForeignKey(
        "accounts.Company", on_delete=models.CASCADE,
        related_name="tax_codes"
    )
    category = models.ForeignKey(
        TaxCategory, on_delete=models.PROTECT,
        related_name="tax_codes"
    )
    code = models.CharField(max_length=30, help_text="e.g. VAT_NORMAL, VAT_EXEMPT")
    name = models.CharField(max_length=100, help_text="e.g. مالیات بر ارزش افزوده عادی")
    rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("10.00"),
        help_text="Tax rate percentage"
    )
    effective_date = models.DateField(
        help_text="Date from which this rate applies"
    )
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("company", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.rate}%)"


class TaxRule(models.Model):
    """
    Business logic container for tax application.

    Per TAX_AND_LEGAL_RULES_IRAN.md §4.3:
    IF Transaction = Sales Invoice AND Item Category = Taxable
    THEN Apply VAT Rule
    """
    company = models.ForeignKey(
        "accounts.Company", on_delete=models.CASCADE,
        related_name="tax_rules"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    tax_code = models.ForeignKey(
        TaxCode, on_delete=models.PROTECT,
        related_name="rules"
    )
    # Rule conditions stored as JSON for flexibility
    # e.g. {"document_type": "sales_invoice", "item_category": "TAXABLE"}
    conditions = models.JSONField(
        default=dict, blank=True,
        help_text="JSON conditions for rule application"
    )
    priority = models.IntegerField(
        default=0, help_text="Higher priority rules are evaluated first"
    )
    version = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "name"]

    def __str__(self):
        return self.name


class TaxTransaction(models.Model):
    """
    Immutable record of every tax calculation.

    Per TAX_AND_LEGAL_RULES_IRAN.md §8: Tax Audit Trail.
    Per TAX_AND_LEGAL_RULES_IRAN.md §18: Database Entity — tax_transactions.
    """
    company = models.ForeignKey(
        "accounts.Company", on_delete=models.CASCADE,
        related_name="tax_transactions"
    )
    fiscal_year = models.ForeignKey(
        "finance.FiscalYear", on_delete=models.PROTECT,
        related_name="tax_transactions"
    )
    tax_code = models.ForeignKey(
        TaxCode, on_delete=models.PROTECT,
        related_name="transactions"
    )
    tax_rule = models.ForeignKey(
        TaxRule, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="transactions"
    )

    # Source document reference
    source_type = models.CharField(max_length=30, help_text="e.g. invoice, receipt")
    source_id = models.IntegerField(null=True, blank=True, help_text="ID of the source document")

    # Tax amounts
    base_amount = models.BigIntegerField(
        help_text="Base amount before tax (Rial)"
    )
    tax_amount = models.BigIntegerField(
        help_text="Calculated tax amount (Rial)"
    )
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Tax rate applied (%)"
    )

    # VAT specifics
    vat_type = models.CharField(
        max_length=20, choices=[
            ("output", "Output VAT (Sales)"),
            ("input", "Input VAT (Purchase)"),
            ("adjustment", "VAT Adjustment"),
        ], default="output"
    )

    # Status
    status = models.CharField(
        max_length=20, choices=[
            ("calculated", "Calculated"),
            ("posted", "Posted to GL"),
            ("reversed", "Reversed"),
        ], default="calculated"
    )

    # Link to journal voucher after posting
    journal_voucher = models.ForeignKey(
        "JournalVoucher", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="tax_transactions"
    )

    description = models.CharField(max_length=500, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="tax_transactions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Tax {self.vat_type} — {self.tax_amount} Rial ({self.tax_code.code})"


# ─── Tax Engine Service ──────────────────────────────────────────


class TaxEngine:
    """
    Central tax calculation engine.

    Per TAX_AND_LEGAL_RULES_IRAN.md §2: Architecture position.
    Per TAX_AND_LEGAL_RULES_IRAN.md §5: VAT Engine.
    Per TAX_AND_LEGAL_RULES_IRAN.md §17: Accounting Integration.
    Per TAX_AND_LEGAL_RULES_IRAN.md §20: Never hard-code tax rates.
    """

    @staticmethod
    def get_applicable_rules(
        company, document_type: str, item_category: str = "TAXABLE"
    ) -> List[TaxRule]:
        """
        Find all active tax rules matching the document and item category.

        Per TAX_AND_LEGAL_RULES_IRAN.md §4.3: Rule evaluation.
        """
        rules = TaxRule.objects.filter(
            company=company,
            is_active=True,
            tax_code__is_active=True,
        ).select_related("tax_code", "tax_code__category").order_by("-priority")

        matched = []
        for rule in rules:
            conditions = rule.conditions or {}
            # Check document_type match
            if conditions.get("document_type") and conditions["document_type"] != document_type:
                continue
            # Check item_category match
            if conditions.get("item_category") and conditions["item_category"] != item_category:
                continue
            matched.append(rule)

        return matched

    @staticmethod
    @transaction.atomic
    def calculate_vat(
        company,
        base_amount: int,
        document_type: str,
        user: Any,
        item_category: str = "TAXABLE",
        source_type: str = "invoice",
        source_id: int = None,
        fiscal_year=None,
    ) -> Dict:
        """
        Calculate VAT for a transaction and record a TaxTransaction.

        Per TAX_AND_LEGAL_RULES_IRAN.md §5.2: Sales Invoice VAT Flow.
        Per TAX_AND_LEGAL_RULES_IRAN.md §5.3: Purchase Invoice VAT Flow.
        Per TAX_AND_LEGAL_RULES_IRAN.md §6: VAT Settlement.

        Returns: {"tax_amount": int, "tax_rate": Decimal, "tax_code": str, "transaction_id": int}
        """
        # Find applicable VAT rules
        rules = TaxEngine.get_applicable_rules(company, document_type, item_category)

        if not rules:
            # Default: no tax applies
            return {
                "tax_amount": 0,
                "tax_rate": Decimal("0.00"),
                "tax_code": None,
                "transaction_id": None,
            }

        # Use highest priority rule (first in list)
        rule = rules[0]
        tax_code = rule.tax_code
        rate = tax_code.rate

        # Calculate tax amount
        tax_amount = int(Decimal(str(base_amount)) * rate / Decimal("100"))

        # Determine VAT type
        if document_type in ("sales_invoice", "sales"):
            vat_type = "output"
        elif document_type in ("purchase_invoice", "purchase"):
            vat_type = "input"
        else:
            vat_type = "output"

        # Record tax transaction — find open fiscal year if not provided
        fy = fiscal_year
        if not fy:
            fy = FiscalYear.objects.filter(company=company, is_closed=False).first()
        if not fy:
            raise ValidationError("No open fiscal year found. Please create a fiscal year first.")

        transaction_record = TaxTransaction.objects.create(
            company=company,
            fiscal_year=fy,
            tax_code=tax_code,
            tax_rule=rule,
            source_type=source_type,
            source_id=source_id,
            base_amount=base_amount,
            tax_amount=tax_amount,
            tax_rate=rate,
            vat_type=vat_type,
            status="calculated",
            description=f"VAT calculated: {rate}% on {base_amount} Rial",
            created_by=user,
        )

        logger.info(
            f"VAT calculated: {tax_amount} Rial ({rate}%) "
            f"for {source_type}#{source_id} by {user.username}"
        )

        return {
            "tax_amount": tax_amount,
            "tax_rate": rate,
            "tax_code": tax_code.code,
            "transaction_id": transaction_record.id,
        }

    @staticmethod
    def get_vat_summary(
        company, fiscal_year_id: Optional[int] = None
    ) -> Dict:
        """
        Get VAT summary for a fiscal period.

        Per TAX_AND_LEGAL_RULES_IRAN.md §6: VAT Settlement Engine.
        Formula: VAT Payable = Output VAT - Input VAT
        """
        fy_filter = {}
        if fiscal_year_id:
            fy_filter["fiscal_year_id"] = fiscal_year_id

        output = TaxTransaction.objects.filter(
            company=company, vat_type="output", status="posted",
            **fy_filter
        ).aggregate(total=Sum("tax_amount"))

        input_vat = TaxTransaction.objects.filter(
            company=company, vat_type="input", status="posted",
            **fy_filter
        ).aggregate(total=Sum("tax_amount"))

        output_total = output["total"] or 0
        input_total = input_vat["total"] or 0
        payable = output_total - input_total

        return {
            "output_vat": output_total,
            "input_vat": input_total,
            "vat_payable": payable,
            "is_settled": payable <= 0,
        }

    @staticmethod
    def calculate_withholding_tax(
        company,
        base_amount: int,
        service_type: str,
        user: Any,
        source_type: str = "payment",
        source_id: int = None,
        fiscal_year=None,
    ) -> Dict:
        """
        Calculate withholding tax for service payments.

        Per TAX_AND_LEGAL_RULES_IRAN.md §14: Withholding Tax Engine.
        Flow: Payment Request → Withholding Rule → Tax Deduction → Tax Liability
        """
        # Find withholding rules for this service type
        rules = TaxEngine.get_applicable_rules(company, "withholding", service_type)

        if not rules:
            return {
                "tax_amount": 0,
                "tax_rate": Decimal("0.00"),
                "tax_code": None,
                "transaction_id": None,
            }

        rule = rules[0]
        tax_code = rule.tax_code
        rate = tax_code.rate
        tax_amount = int(Decimal(str(base_amount)) * rate / Decimal("100"))

        fy = fiscal_year
        if not fy:
            fy = FiscalYear.objects.filter(company=company, is_closed=False).first()
        if not fy:
            raise ValidationError("No open fiscal year found. Please create a fiscal year first.")

        transaction_record = TaxTransaction.objects.create(
            company=company,
            fiscal_year=fy,
            tax_code=tax_code,
            tax_rule=rule,
            source_type=source_type,
            source_id=source_id,
            base_amount=base_amount,
            tax_amount=tax_amount,
            tax_rate=rate,
            vat_type="adjustment",
            status="calculated",
            description=f"Withholding tax: {rate}% on {base_amount} Rial ({service_type})",
            created_by=user,
        )

        return {
            "tax_amount": tax_amount,
            "tax_rate": rate,
            "tax_code": tax_code.code,
            "transaction_id": transaction_record.id,
        }
