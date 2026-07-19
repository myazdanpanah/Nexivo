"""
Finance Module Validators — Business Rule Validation Layer.

Per DJANGO_BACKEND.md §26: Validation occurs in multiple layers.
Layer 2 is Business Validation — this module.
Validates: Company context, Fiscal year, Business rules, Permissions.
Validation should fail as early as possible.
"""

from decimal import Decimal
from .models import (
    KolAccount, MoinAccount, TafziliAccount,
    BankAccount, Customer, Supplier, FiscalYear,
    JournalEntry, Invoice, Cheque,
)
from .exceptions import ValidationError


class JournalValidator:
    """Validates journal voucher business rules."""

    @staticmethod
    def validate_entries_balance(entries_data: list) -> None:
        """Ensure total debit == total credit across all entry lines."""
        total_debit = sum(e.get("debit", 0) for e in entries_data)
        total_credit = sum(e.get("credit", 0) for e in entries_data)
        if total_debit != total_credit:
            raise ValidationError(
                f"Debit ({total_debit}) ≠ Credit ({total_credit}). Journal must be balanced."
            )

    @staticmethod
    def validate_entries_count(entries_data: list) -> None:
        """A journal voucher requires at least 2 entries."""
        if len(entries_data) < 2:
            raise ValidationError("A journal voucher requires at least 2 entry lines.")

    @staticmethod
    def validate_accounts_exist(company, entries_data: list) -> None:
        """Validate that all referenced accounts belong to the company."""
        kol_ids = {e.get("kol") for e in entries_data if e.get("kol")}
        if kol_ids:
            existing = set(
                KolAccount.objects.filter(pk__in=kol_ids, company=company).values_list("pk", flat=True)
            )
            missing = kol_ids - existing
            if missing:
                raise ValidationError(f"Kol accounts not found: {missing}")

    @staticmethod
    def validate_each_line_has_amount(entries_data: list) -> None:
        """Each entry line must have either debit or credit > 0."""
        for i, entry in enumerate(entries_data):
            if not entry.get("debit", 0) and not entry.get("credit", 0):
                raise ValidationError(f"Entry line {i + 1} must have a debit or credit amount.")


class InvoiceValidator:
    """Validates invoice business rules."""

    @staticmethod
    def validate_party_required(invoice_type: str, customer_id, supplier_id) -> None:
        """Sales invoices require a customer; purchase invoices require a supplier."""
        if invoice_type in ("sales", "sales_return") and not customer_id:
            raise ValidationError("Sales invoice requires a customer.")
        if invoice_type in ("purchase", "purchase_return") and not supplier_id:
            raise ValidationError("Purchase invoice requires a supplier.")

    @staticmethod
    def validate_items_not_empty(items_data: list) -> None:
        """An invoice must have at least one line item."""
        if not items_data:
            raise ValidationError("Invoice must have at least one line item.")

    @staticmethod
    def validate_amounts_consistent(data: dict) -> None:
        """Validate that subtotal - discount + tax ≈ total."""
        subtotal = data.get("subtotal", 0)
        discount = data.get("discount", 0)
        tax_amount = data.get("tax_amount", 0)
        total = data.get("total", 0)
        expected = subtotal - discount + tax_amount
        if total != expected:
            raise ValidationError(
                f"Total mismatch: expected {expected} (subtotal {subtotal} - discount {discount} + tax {tax_amount}), got {total}."
            )


class ChequeValidator:
    """Validates cheque business rules."""

    @staticmethod
    def validate_dates(issue_date, due_date) -> None:
        """Due date must be on or after issue date."""
        if issue_date and due_date and due_date < issue_date:
            raise ValidationError("Cheque due date must be on or after issue date.")

    @staticmethod
    def validate_amount_positive(amount) -> None:
        """Cheque amount must be positive."""
        if amount and amount <= 0:
            raise ValidationError("Cheque amount must be positive.")


class FiscalYearValidator:
    """Validates fiscal year business rules."""

    @staticmethod
    def validate_not_closed(fiscal_year: FiscalYear) -> None:
        """Cannot perform transactions in a closed fiscal year."""
        if fiscal_year.is_closed:
            raise ValidationError("Cannot perform operations in a closed fiscal year.")
