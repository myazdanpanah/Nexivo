"""
Finance Module Services — Enterprise ERP Business Logic Layer.

Per DJANGO_BACKEND.md §23: Every business operation is implemented as a Service.
Views must never contain business logic. Services handle:
- Business rules
- Transaction management
- Balance calculations
- Number sequencing
- Audit logging

All services execute inside database transactions.
"""

import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum, F

from typing import Any, Optional

from .models import (
    AccountGroup, KolAccount, MoinAccount, TafziliAccount,
    BankAccount, Customer, Supplier, FiscalYear,
    JournalVoucher, JournalEntry,
    Invoice, InvoiceItem, Receipt, Payment, Cheque,
)
from .validators import (
    JournalValidator, InvoiceValidator, ChequeValidator,
)
from .exceptions import ValidationError  # noqa: F401 — re-exported for backward compat
from .posting import PostingEngine
from .workflow import WorkflowEngine

logger = logging.getLogger(__name__)


class FiscalYearService:
    """Service for fiscal year operations."""

    @staticmethod
    def get_open_fiscal_year(company):
        """Get the current open fiscal year for a company."""
        return FiscalYear.objects.filter(company=company, is_closed=False).first()

    @staticmethod
    def create_fiscal_year(company, data: dict) -> FiscalYear:
        """Create a new fiscal year."""
        if FiscalYear.objects.filter(company=company, name=data["name"]).exists():
            raise ValidationError(f"Fiscal year '{data['name']}' already exists.")
        return FiscalYear.objects.create(company=company, **data)

    @staticmethod
    def close_fiscal_year(fiscal_year: FiscalYear, user):
        """Close a fiscal year — prevents further transactions."""
        if fiscal_year.is_closed:
            raise ValidationError("Fiscal year is already closed.")
        fiscal_year.is_closed = True
        fiscal_year.save(update_fields=["is_closed"])
        logger.info(f"Fiscal year {fiscal_year.name} closed by {user.username}")
        return fiscal_year


class JournalService:
    """Service for journal voucher (سند) operations."""

    @staticmethod
    def _next_voucher_number(company, fiscal_year_id: int) -> int:
        """Calculate the next sequential voucher number."""
        last = JournalVoucher.objects.filter(
            company=company, fiscal_year_id=fiscal_year_id
        ).order_by("-number").first()
        return (last.number + 1) if last else 1

    @staticmethod
    def create_voucher(company: Any, user: Any, data: dict) -> JournalVoucher:
        """Create a journal voucher with entries inside a transaction."""
        # Resolve fiscal year
        fy_id = data.get("fiscal_year")
        if not fy_id:
            fy = FiscalYearService.get_open_fiscal_year(company)
            if not fy:
                raise ValidationError("No open fiscal year found. Create one first.")
            fy_id = fy.id
        else:
            try:
                fy = FiscalYear.objects.get(pk=fy_id, company=company)
            except FiscalYear.DoesNotExist:
                raise ValidationError("Fiscal year not found.")
            if fy.is_closed:
                raise ValidationError("Cannot create voucher in a closed fiscal year.")

        entries_data = data.pop("entries", [])
        # Validate using JournalValidator
        JournalValidator.validate_entries_count(entries_data)
        JournalValidator.validate_entries_balance(entries_data)
        JournalValidator.validate_each_line_has_amount(entries_data)
        JournalValidator.validate_accounts_exist(company, entries_data)

        with transaction.atomic():
            voucher = JournalVoucher.objects.create(
                company=company,
                fiscal_year_id=fy_id,
                number=JournalService._next_voucher_number(company, fy_id),
                date_jalali=data.get("date_jalali", ""),
                date=data.get("date"),
                description=data.get("description", ""),
                source_type=data.get("source_type", "manual"),
                source_id=data.get("source_id"),
                created_by=user,
            )
            for entry_data in entries_data:
                JournalEntry.objects.create(voucher=voucher, **entry_data)

        return voucher

    @staticmethod
    def confirm_voucher(voucher: JournalVoucher, user: Any) -> JournalVoucher:
        """Confirm a journal voucher — validates debit == credit."""
        if voucher.status != "draft":
            raise ValidationError("Only draft vouchers can be confirmed.")

        # Use validator for balance check
        entries = list(voucher.entries.values("debit", "credit"))
        JournalValidator.validate_entries_balance(entries)

        voucher.status = "confirmed"
        voucher.confirmed_by = user
        voucher.save(update_fields=["status", "confirmed_by", "updated_at"])
        logger.info(f"Voucher #{voucher.number} confirmed by {user.username}")
        return voucher


class InvoiceService:
    """Service for invoice (فاکتور) operations."""

    @staticmethod
    def _next_invoice_number(company, fiscal_year, invoice_type: str) -> int:
        """Calculate the next sequential invoice number per type."""
        last = Invoice.objects.filter(
            company=company, fiscal_year=fiscal_year, type=invoice_type
        ).order_by("-number").first()
        return (last.number + 1) if last else 1

    @staticmethod
    def create_invoice(company: Any, user: Any, data: dict) -> Invoice:
        """Create an invoice with line items inside a transaction."""
        fy = FiscalYearService.get_open_fiscal_year(company)
        if not fy:
            raise ValidationError("No open fiscal year found. Create one first.")

        invoice_type = data.get("type", "sales")
        customer_id = data.get("customer")
        supplier_id = data.get("supplier")

        # Validate using InvoiceValidator
        InvoiceValidator.validate_party_required(invoice_type, customer_id, supplier_id)

        # Validate party exists in company
        if customer_id and not Customer.objects.filter(pk=customer_id, company=company).exists():
            raise ValidationError("Customer not found in your company.")
        if supplier_id and not Supplier.objects.filter(pk=supplier_id, company=company).exists():
            raise ValidationError("Supplier not found in your company.")

        items_data = data.pop("items", [])
        InvoiceValidator.validate_items_not_empty(items_data)
        InvoiceValidator.validate_amounts_consistent(data)

        with transaction.atomic():
            invoice = Invoice.objects.create(
                company=company,
                fiscal_year=fy,
                number=InvoiceService._next_invoice_number(company, fy, invoice_type),
                type=invoice_type,
                date_jalali=data.get("date_jalali", ""),
                date=data.get("date"),
                due_date_jalali=data.get("due_date_jalali", ""),
                due_date=data.get("due_date"),
                customer_id=customer_id,
                supplier_id=supplier_id,
                subtotal=data.get("subtotal", 0),
                discount=data.get("discount", 0),
                tax_rate=data.get("tax_rate", Decimal("10.00")),
                tax_amount=data.get("tax_amount", 0),
                total=data.get("total", 0),
                description=data.get("description", ""),
                reference=data.get("reference", ""),
                created_by=user,
            )
            for item_data in items_data:
                InvoiceItem.objects.create(invoice=invoice, **item_data)

        return invoice

    @staticmethod
    def confirm_invoice(invoice: Invoice, user) -> Invoice:
        """
        Confirm an invoice — updates customer/supplier balance and posts to GL.
        Per WORKFLOW_ENGINE.md §62: Uses WorkflowEngine for state transitions.
        Per ACCOUNTING_MODULE.md §8: Posts via PostingEngine.
        """
        if invoice.status == "confirmed":
            return invoice  # idempotent
        if invoice.status != "draft":
            raise ValidationError("Only draft invoices can be confirmed.")

        with transaction.atomic():
            # Execute workflow transition
            WorkflowEngine.execute_transition(
                invoice, "invoice", "confirm", user
            )

            # Update party balance
            if invoice.customer and invoice.type == "sales":
                Customer.objects.filter(pk=invoice.customer_id).update(
                    balance=F("balance") + invoice.total
                )
            elif invoice.customer and invoice.type == "sales_return":
                Customer.objects.filter(pk=invoice.customer_id).update(
                    balance=F("balance") - invoice.total
                )
            elif invoice.supplier and invoice.type == "purchase":
                Supplier.objects.filter(pk=invoice.supplier_id).update(
                    balance=F("balance") + invoice.total
                )
            elif invoice.supplier and invoice.type == "purchase_return":
                Supplier.objects.filter(pk=invoice.supplier_id).update(
                    balance=F("balance") - invoice.total
                )

            # Post to general ledger via PostingEngine
            PostingEngine.post_invoice(invoice, user)

        logger.info(f"Invoice #{invoice.number} confirmed by {user.username}")
        return invoice


class ReceiptService:
    """Service for receipt (رسید دریافت) operations."""

    @staticmethod
    def create_receipt(company, user, data: dict) -> Receipt:
        """Create a receipt for money received from a customer."""
        fy = FiscalYearService.get_open_fiscal_year(company)
        if not fy:
            raise ValidationError("No open fiscal year found.")

        # Validate FKs belong to company
        customer_id = data.get("customer")
        bank_account_id = data.get("bank_account")
        if customer_id and not Customer.objects.filter(pk=customer_id, company=company).exists():
            raise ValidationError("Customer not found in your company.")
        if bank_account_id and not BankAccount.objects.filter(pk=bank_account_id, company=company).exists():
            raise ValidationError("Bank account not found in your company.")

        last = Receipt.objects.filter(company=company, fiscal_year=fy).order_by("-number").first()
        number = (last.number + 1) if last else 1

        with transaction.atomic():
            receipt = Receipt.objects.create(
                company=company,
                fiscal_year=fy,
                number=number,
                date_jalali=data.get("date_jalali", ""),
                date=data.get("date"),
                customer_id=customer_id,
                bank_account_id=bank_account_id,
                amount=data.get("amount", 0),
                payment_method=data.get("payment_method", "cash"),
                reference=data.get("reference", ""),
                description=data.get("description", ""),
                invoice_id=data.get("invoice"),
                created_by=user,
            )
            # Post to general ledger via PostingEngine
            PostingEngine.post_receipt(receipt, user)
        return receipt


class PaymentService:
    """Service for payment (پرداختی) operations."""

    @staticmethod
    def create_payment(company, user, data: dict) -> Payment:
        """Create a payment for money paid to a supplier."""
        fy = FiscalYearService.get_open_fiscal_year(company)
        if not fy:
            raise ValidationError("No open fiscal year found.")

        # Validate FKs belong to company
        supplier_id = data.get("supplier")
        bank_account_id = data.get("bank_account")
        if supplier_id and not Supplier.objects.filter(pk=supplier_id, company=company).exists():
            raise ValidationError("Supplier not found in your company.")
        if bank_account_id and not BankAccount.objects.filter(pk=bank_account_id, company=company).exists():
            raise ValidationError("Bank account not found in your company.")

        last = Payment.objects.filter(company=company, fiscal_year=fy).order_by("-number").first()
        number = (last.number + 1) if last else 1

        with transaction.atomic():
            payment = Payment.objects.create(
                company=company,
                fiscal_year=fy,
                number=number,
                date_jalali=data.get("date_jalali", ""),
                date=data.get("date"),
                supplier_id=supplier_id,
                bank_account_id=bank_account_id,
                amount=data.get("amount", 0),
                payment_method=data.get("payment_method", "cash"),
                reference=data.get("reference", ""),
                description=data.get("description", ""),
                invoice_id=data.get("invoice"),
                created_by=user,
            )
            # Post to general ledger via PostingEngine
            PostingEngine.post_payment(payment, user)
        return payment


class ChequeService:
    """Service for cheque (چک) operations."""

    @staticmethod
    def create_cheque(company: Any, data: dict) -> Cheque:
        """Create a cheque record."""
        # Validate using ChequeValidator
        if data.get("amount"):
            ChequeValidator.validate_amount_positive(data["amount"])
        if data.get("issue_date") and data.get("due_date"):
            ChequeValidator.validate_dates(data["issue_date"], data["due_date"])

        # Validate FKs belong to company
        customer_id = data.get("customer")
        supplier_id = data.get("supplier")
        if customer_id and not Customer.objects.filter(pk=customer_id, company=company).exists():
            raise ValidationError("Customer not found in your company.")
        if supplier_id and not Supplier.objects.filter(pk=supplier_id, company=company).exists():
            raise ValidationError("Supplier not found in your company.")

        with transaction.atomic():
            cheque = Cheque.objects.create(company=company, **data)
        return cheque
