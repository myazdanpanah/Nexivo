"""
Tests for Finance module — CRUD, module gates, invoice confirmation,
journal voucher balancing, customer/supplier search, financial summary.

Updated to use standard API response format per API_SPECIFICATION.md §6-§8.
All responses now follow: {"success": bool, "data": ..., "message": str, "errors": [...]}
"""

import datetime
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests_helpers import create_test_company, create_test_user
from .models import (
    AccountGroup, KolAccount, MoinAccount, TafziliAccount,
    BankAccount, Customer, Supplier, FiscalYear,
    JournalVoucher, JournalEntry,
    Invoice, InvoiceItem, Receipt, Payment, Cheque,
)

User = get_user_model()


class FinanceModuleGateTests(TestCase):
    """Tests that the finance module gate blocks unprivileged requests."""

    def setUp(self):
        self.client = APIClient()
        # Company WITHOUT finance module enabled
        self.no_finance_company = create_test_company(
            name="No Finance Co",
            enabled_modules=["bi_dashboard", "datasets"],
        )
        self.user = create_test_user(
            username="nofin",
            company=self.no_finance_company,
            role="ceo",
        )
        self.url = reverse("customer-list")

    def test_module_disabled_returns_403(self):
        """Requests to finance endpoints return 403 when module is disabled."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("success", response.data)
        self.assertFalse(response.data["success"])


class FiscalYearTests(TestCase):
    """Tests for FiscalYear CRUD."""

    def setUp(self):
        self.client = APIClient()
        self.company = create_test_company()
        self.user = create_test_user(company=self.company, role="ceo")
        self.url = reverse("fy-list")

    def test_list_fiscal_years(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    def test_create_fiscal_year(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {
            "name": "۱۴۰۴",
            "start_date_jalali": "1403/01/01",
            "end_date_jalali": "1404/01/01",
            "start_date": "2024-03-20",
            "end_date": "2025-03-19",
        }, format="json")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["name"], "۱۴۰۴")


class CustomerTests(TestCase):
    """Tests for Customer CRUD and search."""

    def setUp(self):
        self.client = APIClient()
        self.company = create_test_company()
        self.user = create_test_user(company=self.company, role="ceo")
        self.url = reverse("customer-list")
        self.customer = Customer.objects.create(
            company=self.company,
            name="شرکت آلفا",
            national_id="12345678901",
        )

    def test_list_customers(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 1)

    def test_create_customer(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {
            "name": "شرکت بتا",
            "national_id": "10987654321",
        }, format="json")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["name"], "شرکت بتا")

    def test_search_customer_by_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"{self.url}?q=آلفا")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)

    def test_search_customer_by_national_id(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"{self.url}?q=12345")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)

    def test_customer_detail(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("customer-detail", args=[self.customer.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["name"], "شرکت آلفا")

    def test_delete_customer(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("customer-detail", args=[self.customer.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Customer.objects.filter(pk=self.customer.pk).exists())


class SupplierTests(TestCase):
    """Tests for Supplier CRUD and search."""

    def setUp(self):
        self.client = APIClient()
        self.company = create_test_company()
        self.user = create_test_user(company=self.company, role="ceo")
        self.url = reverse("supplier-list")
        self.supplier = Supplier.objects.create(
            company=self.company,
            name="تأمین‌کننده گاما",
            national_id="11111111111",
        )

    def test_list_suppliers(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 1)

    def test_create_supplier(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {
            "name": "تأمین‌کننده دلتا",
        }, format="json")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(response.data["success"])

    def test_search_supplier(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"{self.url}?q=گاما")
        self.assertEqual(len(response.data["data"]), 1)


class InvoiceTests(TestCase):
    """Tests for Invoice CRUD, auto-numbering, and confirmation."""

    def setUp(self):
        self.client = APIClient()
        self.company = create_test_company()
        self.user = create_test_user(company=self.company, role="ceo")
        self.fy = FiscalYear.objects.create(
            company=self.company,
            name="۱۴۰۴",
            start_date_jalali="1403/01/01",
            end_date_jalali="1404/01/01",
            start_date=datetime.date(2024, 3, 20),
            end_date=datetime.date(2025, 3, 19),
        )
        self.customer = Customer.objects.create(
            company=self.company, name="مشتری تست",
        )
        # Create chart of accounts required by PostingEngine
        self.group_assets = AccountGroup.objects.create(
            company=self.company, code="1", name="دارایی‌ها"
        )
        self.group_liabilities = AccountGroup.objects.create(
            company=self.company, code="2", name="بدهی‌ها"
        )
        self.group_revenue = AccountGroup.objects.create(
            company=self.company, code="4", name="درآمدها"
        )
        # Kol accounts used by PostingEngine
        self.kol_bank = KolAccount.objects.create(
            company=self.company, group=self.group_assets, code="102",
            name="بانک", account_type="asset", normal_balance="debit",
        )
        self.kol_inventory = KolAccount.objects.create(
            company=self.company, group=self.group_assets, code="111",
            name="موجودی کالا", account_type="asset", normal_balance="debit",
        )
        self.kol_customer = KolAccount.objects.create(
            company=self.company, group=self.group_assets, code="131",
            name="حساب مشتریان", account_type="asset", normal_balance="debit",
        )
        self.kol_input_vat = KolAccount.objects.create(
            company=self.company, group=self.group_assets, code="133",
            name="مالیات پرداختی", account_type="asset", normal_balance="debit",
        )
        self.kol_supplier = KolAccount.objects.create(
            company=self.company, group=self.group_liabilities, code="231",
            name="حساب تأمین‌کنندگان", account_type="liability", normal_balance="credit",
        )
        self.kol_vat = KolAccount.objects.create(
            company=self.company, group=self.group_liabilities, code="341",
            name="مالیات بر ارزش افزوده", account_type="liability", normal_balance="credit",
        )
        self.kol_revenue = KolAccount.objects.create(
            company=self.company, group=self.group_revenue, code="401",
            name="درآمد فروش", account_type="revenue", normal_balance="credit",
        )
        self.url = reverse("invoice-list")

    def test_create_invoice(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {
            "type": "sales",
            "date_jalali": "1404/04/01",
            "date": "2025-06-21",
            "customer": self.customer.pk,
            "subtotal": 10000000,
            "tax_rate": 10.00,
            "tax_amount": 1000000,
            "total": 11000000,
            "items": [{
                "description": "کالای تست",
                "quantity": 1,
                "unit_price": 10000000,
                "total": 10000000,
            }],
        }, format="json")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["number"], 1)
        self.assertEqual(response.data["data"]["status"], "draft")

    def test_auto_numbering(self):
        """Invoice numbers auto-increment per fiscal year and type."""
        self.client.force_authenticate(user=self.user)
        for i in range(3):
            resp = self.client.post(self.url, {
                "type": "sales",
                "date_jalali": f"1404/04/{i+1:02d}",
                "date": f"2025-06-{21+i:02d}",
                "customer": self.customer.pk,
                "subtotal": 1000000,
                "tax_amount": 0,
                "total": 1000000,
                "items": [{"description": "test", "quantity": 1, "unit_price": 1000000, "total": 1000000}],
            }, format="json")
            self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        invoices = Invoice.objects.filter(company=self.company, type="sales")
        numbers = list(invoices.values_list("number", flat=True))
        self.assertEqual(sorted(numbers), [1, 2, 3])

    def test_confirm_invoice_updates_customer_balance(self):
        """Confirming a sales invoice increases customer balance."""
        self.client.force_authenticate(user=self.user)
        create_resp = self.client.post(self.url, {
            "type": "sales",
            "date_jalali": "1404/04/01",
            "date": "2025-06-21",
            "customer": self.customer.pk,
            "subtotal": 5000000,
            "tax_amount": 500000,
            "total": 5500000,
            "items": [{"description": "test", "quantity": 1, "unit_price": 5000000, "total": 5000000}],
        }, format="json")
        self.assertIn(create_resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        invoice_id = create_resp.data["data"]["id"]
        confirm_url = reverse("invoice-confirm", args=[invoice_id])
        response = self.client.post(confirm_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["status"], "confirmed")
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.balance, 5500000)


class JournalVoucherTests(TestCase):
    """Tests for journal voucher CRUD and confirmation."""

    def setUp(self):
        self.client = APIClient()
        self.company = create_test_company()
        self.user = create_test_user(company=self.company, role="ceo")
        self.fy = FiscalYear.objects.create(
            company=self.company,
            name="۱۴۰۴",
            start_date_jalali="1403/01/01",
            end_date_jalali="1404/01/01",
            start_date=datetime.date(2024, 3, 20),
            end_date=datetime.date(2025, 3, 19),
        )
        # Create minimal chart of accounts for entries
        self.group = AccountGroup.objects.create(
            company=self.company, code="1", name="دارایی‌ها",
        )
        self.kol_cash = KolAccount.objects.create(
            company=self.company, group=self.group, code="101",
            name="صندوق", account_type="asset", normal_balance="debit",
        )
        self.kol_bank = KolAccount.objects.create(
            company=self.company, group=self.group, code="102",
            name="بانک", account_type="asset", normal_balance="debit",
        )
        self.url = reverse("voucher-list")

    def test_create_voucher_with_entries(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {
            "date_jalali": "1404/04/01",
            "date": "2025-06-21",
            "description": "انتقال وجه",
            "entries": [
                {"kol": self.kol_bank.pk, "debit": 5000000, "credit": 0},
                {"kol": self.kol_cash.pk, "debit": 0, "credit": 5000000},
            ],
        }, format="json")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["number"], 1)

    def test_confirm_balanced_voucher(self):
        """A balanced voucher (debit == credit) can be confirmed."""
        self.client.force_authenticate(user=self.user)
        create_resp = self.client.post(self.url, {
            "date_jalali": "1404/04/01",
            "date": "2025-06-21",
            "description": "تراکنش",
            "entries": [
                {"kol": self.kol_bank.pk, "debit": 1000000, "credit": 0},
                {"kol": self.kol_cash.pk, "debit": 0, "credit": 1000000},
            ],
        }, format="json")
        self.assertIn(create_resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        voucher_id = create_resp.data["data"]["id"]
        confirm_url = reverse("voucher-confirm", args=[voucher_id])
        response = self.client.post(confirm_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["status"], "confirmed")

    def test_confirm_unbalanced_voucher_fails(self):
        """An unbalanced voucher (debit != credit) cannot be confirmed."""
        self.client.force_authenticate(user=self.user)
        # The service layer validates balance at creation time and raises 422
        response = self.client.post(self.url, {
            "date_jalali": "1404/04/01",
            "date": "2025-06-21",
            "description": "عدم تطابق",
            "entries": [
                {"kol": self.kol_bank.pk, "debit": 1000000, "credit": 0},
                {"kol": self.kol_cash.pk, "debit": 0, "credit": 500000},
            ],
        }, format="json")
        # Service validates balance at creation — returns 422
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)


class ChequeTests(TestCase):
    """Tests for Cheque CRUD and filtering."""

    def setUp(self):
        self.client = APIClient()
        self.company = create_test_company()
        self.user = create_test_user(company=self.company, role="ceo")
        self.url = reverse("cheque-list")
        self.cheque = Cheque.objects.create(
            company=self.company,
            cheque_type="received",
            number="123456",
            bank_name="بانک ملت",
            amount=2000000,
            issue_date_jalali="1404/04/01",
            issue_date=datetime.date(2025, 6, 21),
            due_date_jalali="1404/05/01",
            due_date=datetime.date(2025, 7, 22),
        )

    def test_list_cheques(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 1)

    def test_filter_by_type(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"{self.url}?cheque_type=received")
        self.assertEqual(len(response.data["data"]), 1)
        response = self.client.get(f"{self.url}?cheque_type=issued")
        self.assertEqual(len(response.data["data"]), 0)


class FinanceSummaryTests(TestCase):
    """Tests for the finance_summary endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.company = create_test_company()
        self.user = create_test_user(company=self.company, role="ceo")
        self.url = reverse("finance-summary")

    def test_summary_with_no_data(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["total_sales"], 0)
        self.assertEqual(data["total_receipts"], 0)

    def test_summary_no_fiscal_year(self):
        """When no fiscal year exists, summary returns zeros."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["data"]["fiscal_year"])


class TrialBalanceTests(TestCase):
    """Tests for the trial_balance endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.company = create_test_company()
        self.user = create_test_user(company=self.company, role="ceo")
        self.url = reverse("trial-balance")

    def test_trial_balance_empty(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertTrue(response.data["data"]["is_balanced"])
        self.assertEqual(response.data["data"]["total_debit"], 0)
        self.assertEqual(response.data["data"]["total_credit"], 0)
