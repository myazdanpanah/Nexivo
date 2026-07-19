"""
Finance Module Selectors — Read-Only Query Services.

Per DJANGO_BACKEND.md §25: Selectors are read-only query services.
Purpose: Dashboard queries, reports, search, complex filters.
Selectors never modify data.
"""

from django.db.models import Sum, Q, Count, F
from .models import (
    AccountGroup, KolAccount, MoinAccount, TafziliAccount,
    BankAccount, Customer, Supplier, FiscalYear,
    JournalVoucher, JournalEntry,
    Invoice, InvoiceItem, Receipt, Payment, Cheque,
)


class AccountSelector:
    """Read-only queries for Chart of Accounts."""

    @staticmethod
    def get_company_accounts(company):
        """Return all active accounts for a company."""
        return {
            "groups": AccountGroup.objects.filter(company=company).order_by("code"),
            "kols": KolAccount.objects.filter(company=company, is_active=True)
                     .select_related("group").order_by("code"),
            "moins": MoinAccount.objects.filter(company=company, is_active=True)
                      .select_related("kol").order_by("code"),
            "tafzilis": TafziliAccount.objects.filter(company=company, is_active=True)
                        .order_by("code"),
        }

    @staticmethod
    def get_account_tree(company):
        """Build the full account tree: Group → Kol → Moin → Tafzili."""
        groups = AccountGroup.objects.filter(company=company).order_by("code")
        kols_by_group = {}
        for kol in KolAccount.objects.filter(company=company).select_related("group").order_by("code"):
            kols_by_group.setdefault(kol.group_id, []).append(kol)

        moins_by_kol = {}
        for moin in MoinAccount.objects.filter(company=company).select_related("kol").order_by("code"):
            moins_by_kol.setdefault(moin.kol_id, []).append(moin)

        tafzili_by_moin = {}
        for t in TafziliAccount.objects.filter(
            company=company, linked_moin_accounts__isnull=False
        ).prefetch_related("linked_moin_accounts").order_by("code"):
            for m in t.linked_moin_accounts.all():
                tafzili_by_moin.setdefault(m.id, []).append(t)

        return groups, kols_by_group, moins_by_kol, tafzili_by_moin


class CustomerSelector:
    """Read-only queries for customers."""

    @staticmethod
    def search(company, query: str = ""):
        """Search customers by name or national_id."""
        qs = Customer.objects.filter(company=company, is_active=True)
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(national_id__icontains=query))
        return qs.order_by("name")

    @staticmethod
    def get_balances(company):
        """List all customer balances."""
        return Customer.objects.filter(
            company=company, is_active=True
        ).order_by("name").values("id", "name", "national_id", "balance")


class SupplierSelector:
    """Read-only queries for suppliers."""

    @staticmethod
    def search(company, query: str = ""):
        """Search suppliers by name or national_id."""
        qs = Supplier.objects.filter(company=company, is_active=True)
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(national_id__icontains=query))
        return qs.order_by("name")

    @staticmethod
    def get_balances(company):
        """List all supplier balances."""
        return Supplier.objects.filter(
            company=company, is_active=True
        ).order_by("name").values("id", "name", "national_id", "balance")


class FinanceDashboardSelector:
    """Read-only queries for the finance dashboard KPIs."""

    @staticmethod
    def get_summary(company):
        """Return aggregated financial summary for the dashboard."""
        fy = FiscalYear.objects.filter(company=company, is_closed=False).first()
        if not fy:
            return {
                "fiscal_year": None,
                "total_sales": 0,
                "total_purchases": 0,
                "total_receipts": 0,
                "total_payments": 0,
                "open_cheques_received": 0,
                "open_cheques_issued": 0,
                "bank_balance": 0,
                "customers_count": 0,
                "suppliers_count": 0,
            }

        total_sales = (
            Invoice.objects.filter(company=company, fiscal_year=fy, type="sales", status="confirmed")
            .aggregate(s=Sum("total"))["s"] or 0
        )
        total_purchases = (
            Invoice.objects.filter(company=company, fiscal_year=fy, type="purchase", status="confirmed")
            .aggregate(s=Sum("total"))["s"] or 0
        )
        total_receipts = (
            Receipt.objects.filter(company=company, fiscal_year=fy, status="confirmed")
            .aggregate(s=Sum("amount"))["s"] or 0
        )
        total_payments = (
            Payment.objects.filter(company=company, fiscal_year=fy, status="confirmed")
            .aggregate(s=Sum("amount"))["s"] or 0
        )
        open_cheques_received = (
            Cheque.objects.filter(company=company, cheque_type="received", status="pending")
            .aggregate(s=Sum("amount"))["s"] or 0
        )
        open_cheques_issued = (
            Cheque.objects.filter(company=company, cheque_type="issued", status="pending")
            .aggregate(s=Sum("amount"))["s"] or 0
        )
        bank_balance = (
            BankAccount.objects.filter(company=company, is_active=True)
            .aggregate(s=Sum("current_balance"))["s"] or 0
        )

        return {
            "fiscal_year": fy,
            "total_sales": total_sales,
            "total_purchases": total_purchases,
            "total_receipts": total_receipts,
            "total_payments": total_payments,
            "open_cheques_received": open_cheques_received,
            "open_cheques_issued": open_cheques_issued,
            "bank_balance": bank_balance,
            "customers_count": Customer.objects.filter(company=company, is_active=True).count(),
            "suppliers_count": Supplier.objects.filter(company=company, is_active=True).count(),
        }


class JournalSelector:
    """Read-only queries for journal vouchers."""

    @staticmethod
    def list_vouchers(company, fiscal_year_id=None, status_filter=None):
        """List journal vouchers with optional filters."""
        qs = JournalVoucher.objects.filter(company=company).select_related(
            "fiscal_year", "created_by"
        )
        if fiscal_year_id:
            qs = qs.filter(fiscal_year_id=fiscal_year_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class InvoiceSelector:
    """Read-only queries for invoices."""

    @staticmethod
    def list_invoices(company, invoice_type=None, status_filter=None):
        """List invoices with optional type/status filters."""
        qs = Invoice.objects.filter(company=company).select_related(
            "fiscal_year", "customer", "supplier", "created_by"
        )
        if invoice_type:
            qs = qs.filter(type=invoice_type)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs
