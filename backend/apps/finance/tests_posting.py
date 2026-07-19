"""
Tests for PostingEngine and WorkflowEngine — Enterprise ERP Core.

Per AI_AGENT_IMPLEMENTATION_GUIDE.md §16: Every feature requires tests.
Required test types: Unit Tests, Integration Tests, Workflow Tests.
"""

import datetime
from decimal import Decimal
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
from .posting import PostingEngine, LedgerService
from .workflow import WorkflowEngine, WorkflowState, DOCUMENT_TRANSITIONS
from .exceptions import ValidationError

User = get_user_model()


class PostingEngineTestBase(TestCase):
    """Shared setUp for PostingEngine tests — creates full chart of accounts."""

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

        # Create account groups
        self.group_assets = AccountGroup.objects.create(
            company=self.company, code="1", name="دارایی‌ها"
        )
        self.group_liabilities = AccountGroup.objects.create(
            company=self.company, code="2", name="بدهی‌ها"
        )
        self.group_revenue = AccountGroup.objects.create(
            company=self.company, code="4", name="درآمدها"
        )
        self.group_expenses = AccountGroup.objects.create(
            company=self.company, code="5", name="هزینه‌ها"
        )

        # Create Kol accounts
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

        # Create parties
        self.customer = Customer.objects.create(
            company=self.company, name="مشتری تست", national_id="12345678901",
        )
        self.supplier = Supplier.objects.create(
            company=self.company, name="تأمین‌کننده تست", national_id="11111111111",
        )
        self.bank_account = BankAccount.objects.create(
            company=self.company, name="حساب بانک ملت",
            account_type="bank", bank_name="ملت",
            account_number="1234567890",
        )


class PostingEngineInvoiceTests(PostingEngineTestBase):
    """Tests for PostingEngine.post_invoice."""

    def test_post_sales_invoice_creates_voucher(self):
        """Posting a sales invoice creates a journal voucher with correct entries."""
        invoice = Invoice.objects.create(
            company=self.company, fiscal_year=self.fy,
            number=1, type="sales",
            date_jalali="1404/04/01", date=datetime.date(2025, 6, 21),
            customer=self.customer,
            subtotal=10000000, tax_amount=1000000, total=11000000,
        )
        voucher = PostingEngine.post_invoice(invoice, self.user)

        self.assertIsNotNone(voucher)
        self.assertEqual(voucher.status, "confirmed")
        self.assertEqual(voucher.source_type, "invoice")
        self.assertEqual(voucher.source_id, invoice.id)

        # Verify entries
        entries = list(voucher.entries.select_related("kol").order_by("kol__code"))
        self.assertGreaterEqual(len(entries), 2)

        # Check debit/credit totals balance
        total_debit = sum(e.debit for e in entries)
        total_credit = sum(e.credit for e in entries)
        self.assertEqual(total_debit, total_credit)
        self.assertEqual(total_debit, 11000000)

        # Verify invoice is linked
        invoice.refresh_from_db()
        self.assertEqual(invoice.journal_voucher_id, voucher.id)

    def test_post_sales_invoice_with_tax_creates_vat_entry(self):
        """Posting a sales invoice with tax creates a VAT payable entry."""
        invoice = Invoice.objects.create(
            company=self.company, fiscal_year=self.fy,
            number=2, type="sales",
            date_jalali="1404/04/02", date=datetime.date(2025, 6, 22),
            customer=self.customer,
            subtotal=10000000, tax_amount=1000000, total=11000000,
        )
        voucher = PostingEngine.post_invoice(invoice, self.user)

        # Check for VAT entry
        vat_entry = voucher.entries.filter(kol=self.kol_vat).first()
        self.assertIsNotNone(vat_entry)
        self.assertEqual(vat_entry.credit, 1000000)

    def test_post_purchase_invoice_creates_entries(self):
        """Posting a purchase invoice creates correct debit/credit entries."""
        invoice = Invoice.objects.create(
            company=self.company, fiscal_year=self.fy,
            number=3, type="purchase",
            date_jalali="1404/04/03", date=datetime.date(2025, 6, 23),
            supplier=self.supplier,
            subtotal=5000000, tax_amount=500000, total=5500000,
        )
        voucher = PostingEngine.post_invoice(invoice, self.user)

        self.assertIsNotNone(voucher)
        entries = list(voucher.entries.all())
        self.assertGreaterEqual(len(entries), 2)

        # Verify inventory debit
        inv_entry = voucher.entries.filter(kol=self.kol_inventory).first()
        self.assertIsNotNone(inv_entry)
        self.assertEqual(inv_entry.debit, 5000000)

        # Verify supplier credit
        sup_entry = voucher.entries.filter(kol=self.kol_supplier).first()
        self.assertIsNotNone(sup_entry)
        self.assertEqual(sup_entry.credit, 5500000)

    def test_post_invoice_idempotent(self):
        """Posting the same invoice twice returns the same voucher."""
        invoice = Invoice.objects.create(
            company=self.company, fiscal_year=self.fy,
            number=4, type="sales",
            date_jalali="1404/04/04", date=datetime.date(2025, 6, 24),
            customer=self.customer,
            subtotal=1000000, total=1100000,
        )
        voucher1 = PostingEngine.post_invoice(invoice, self.user)
        voucher2 = PostingEngine.post_invoice(invoice, self.user)
        self.assertEqual(voucher1.id, voucher2.id)

    def test_post_invoice_missing_kol_account_raises_error(self):
        """Posting fails if required Kol account doesn't exist."""
        # Delete the customer receivable account
        KolAccount.objects.filter(company=self.company, code="131").delete()

        invoice = Invoice.objects.create(
            company=self.company, fiscal_year=self.fy,
            number=5, type="sales",
            date_jalali="1404/04/05", date=datetime.date(2025, 6, 25),
            customer=self.customer,
            subtotal=1000000, total=1100000,
        )
        with self.assertRaises(ValidationError) as ctx:
            PostingEngine.post_invoice(invoice, self.user)
        self.assertIn("131", str(ctx.exception))

    def test_post_invoice_no_fiscal_year_raises_error(self):
        """Posting fails if no open fiscal year exists."""
        self.fy.is_closed = True
        self.fy.save()

        invoice = Invoice.objects.create(
            company=self.company, fiscal_year=self.fy,
            number=6, type="sales",
            date_jalali="1404/04/06", date=datetime.date(2025, 6, 26),
            customer=self.customer,
            subtotal=1000000, total=1100000,
        )
        with self.assertRaises(ValidationError) as ctx:
            PostingEngine.post_invoice(invoice, self.user)
        self.assertIn("fiscal year", str(ctx.exception).lower())


class PostingEngineReceiptTests(PostingEngineTestBase):
    """Tests for PostingEngine.post_receipt."""

    def test_post_receipt_creates_voucher(self):
        """Posting a receipt creates a journal voucher."""
        receipt = Receipt.objects.create(
            company=self.company, fiscal_year=self.fy,
            number=1, date_jalali="1404/04/01", date=datetime.date(2025, 6, 21),
            customer=self.customer, bank_account=self.bank_account,
            amount=5000000, payment_method="bank_transfer",
        )
        voucher = PostingEngine.post_receipt(receipt, self.user)

        self.assertIsNotNone(voucher)
        self.assertEqual(voucher.source_type, "receipt")
        entries = list(voucher.entries.all())
        self.assertEqual(len(entries), 2)

        total_debit = sum(e.debit for e in entries)
        total_credit = sum(e.credit for e in entries)
        self.assertEqual(total_debit, total_credit)
        self.assertEqual(total_debit, 5000000)


class PostingEnginePaymentTests(PostingEngineTestBase):
    """Tests for PostingEngine.post_payment."""

    def test_post_payment_creates_voucher(self):
        """Posting a payment creates a journal voucher."""
        payment = Payment.objects.create(
            company=self.company, fiscal_year=self.fy,
            number=1, date_jalali="1404/04/01", date=datetime.date(2025, 6, 21),
            supplier=self.supplier, bank_account=self.bank_account,
            amount=3000000, payment_method="bank_transfer",
        )
        voucher = PostingEngine.post_payment(payment, self.user)

        self.assertIsNotNone(voucher)
        self.assertEqual(voucher.source_type, "payment")
        entries = list(voucher.entries.all())
        self.assertEqual(len(entries), 2)

        total_debit = sum(e.debit for e in entries)
        total_credit = sum(e.credit for e in entries)
        self.assertEqual(total_debit, total_credit)
        self.assertEqual(total_debit, 3000000)


class LedgerServiceTests(PostingEngineTestBase):
    """Tests for LedgerService read-only queries."""

    def test_trial_balance_balanced(self):
        """Trial balance of posted transactions is balanced."""
        # Post a sales invoice
        invoice = Invoice.objects.create(
            company=self.company, fiscal_year=self.fy,
            number=1, type="sales",
            date_jalali="1404/04/01", date=datetime.date(2025, 6, 21),
            customer=self.customer,
            subtotal=10000000, tax_amount=1000000, total=11000000,
        )
        PostingEngine.post_invoice(invoice, self.user)

        result = LedgerService.get_trial_balance(self.company)
        self.assertTrue(result["is_balanced"])
        self.assertEqual(result["total_debit"], result["total_credit"])

    def test_account_balance(self):
        """Account balance returns correct debit/credit totals."""
        invoice = Invoice.objects.create(
            company=self.company, fiscal_year=self.fy,
            number=1, type="sales",
            date_jalali="1404/04/01", date=datetime.date(2025, 6, 21),
            customer=self.customer,
            subtotal=10000000, tax_amount=1000000, total=11000000,
        )
        PostingEngine.post_invoice(invoice, self.user)

        result = LedgerService.get_account_balance(self.company, self.kol_customer.id)
        self.assertEqual(result["total_debit"], 11000000)
        self.assertEqual(result["total_credit"], 0)
        self.assertEqual(result["balance"], 11000000)

    def test_trial_balance_with_no_data(self):
        """Trial balance with no data returns zeros."""
        result = LedgerService.get_trial_balance(self.company)
        self.assertTrue(result["is_balanced"])
        self.assertEqual(result["total_debit"], 0)
        self.assertEqual(result["total_credit"], 0)


class WorkflowEngineTests(TestCase):
    """Tests for WorkflowEngine state machine."""

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
        # Create minimal chart of accounts
        group = AccountGroup.objects.create(
            company=self.company, code="1", name="دارایی‌ها"
        )
        self.kol_bank = KolAccount.objects.create(
            company=self.company, group=group, code="102",
            name="بانک", account_type="asset", normal_balance="debit",
        )
        self.kol_customer = KolAccount.objects.create(
            company=self.company, group=group, code="131",
            name="حساب مشتریان", account_type="asset", normal_balance="debit",
        )
        self.kol_revenue = KolAccount.objects.create(
            company=self.company, group=group, code="401",
            name="درآمد فروش", account_type="revenue", normal_balance="credit",
        )
        self.kol_vat = KolAccount.objects.create(
            company=self.company, group=group, code="341",
            name="مالیات", account_type="liability", normal_balance="credit",
        )
        self.customer = Customer.objects.create(
            company=self.company, name="مشتری تست",
        )

    def test_valid_transition_draft_to_confirmed(self):
        """Draft → confirmed is a valid transition for invoice."""
        transitions = WorkflowEngine.get_valid_transitions("invoice", "draft")
        actions = [t["action"] for t in transitions]
        self.assertIn("confirm", actions)

    def test_valid_transition_draft_to_cancelled(self):
        """Draft → cancelled is a valid transition for invoice."""
        transitions = WorkflowEngine.get_valid_transitions("invoice", "draft")
        actions = [t["action"] for t in transitions]
        self.assertIn("cancel", actions)

    def test_invalid_transition_raises_error(self):
        """Confirming from 'confirmed' state raises ValidationError."""
        with self.assertRaises(ValidationError):
            WorkflowEngine.validate_transition("invoice", "confirmed", "confirm")

    def test_execute_transition_updates_status(self):
        """Executing a transition updates the document's status."""
        invoice = Invoice.objects.create(
            company=self.company, fiscal_year=self.fy,
            number=1, type="sales",
            date_jalali="1404/04/01", date=datetime.date(2025, 6, 21),
            customer=self.customer,
            subtotal=10000000, tax_amount=1000000, total=11000000,
        )
        self.assertEqual(invoice.status, "draft")

        result = WorkflowEngine.execute_transition(
            invoice, "invoice", "confirm", self.user
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "confirmed")
        self.assertEqual(result["previous_state"], "draft")
        self.assertEqual(result["new_state"], "confirmed")

    def test_execute_cancel_transition(self):
        """Executing cancel from draft sets status to cancelled."""
        invoice = Invoice.objects.create(
            company=self.company, fiscal_year=self.fy,
            number=2, type="sales",
            date_jalali="1404/04/02", date=datetime.date(2025, 6, 22),
            customer=self.customer,
            subtotal=5000000, total=5500000,
        )
        WorkflowEngine.execute_transition(
            invoice, "invoice", "cancel", self.user
        )
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "cancelled")

    def test_all_document_types_have_transitions(self):
        """All document types have defined transitions."""
        for doc_type in ["invoice", "voucher", "receipt", "payment"]:
            self.assertIn(doc_type, DOCUMENT_TRANSITIONS)
            transitions = DOCUMENT_TRANSITIONS[doc_type]
            self.assertGreater(len(transitions), 0)

    def test_transition_returns_metadata(self):
        """Transition result includes metadata."""
        invoice = Invoice.objects.create(
            company=self.company, fiscal_year=self.fy,
            number=3, type="sales",
            date_jalali="1404/04/03", date=datetime.date(2025, 6, 23),
            customer=self.customer,
            subtotal=1000000, total=1100000,
        )
        result = WorkflowEngine.execute_transition(
            invoice, "invoice", "confirm", self.user, comment="Test"
        )
        self.assertEqual(result["action"], "confirm")
        self.assertEqual(result["user"], self.user.username)
        self.assertEqual(result["comment"], "Test")
        self.assertIn("timestamp", result)


class IntegrationPostingWorkflowTests(PostingEngineTestBase):
    """Integration tests: PostingEngine + WorkflowEngine + Views."""

    def test_invoice_confirm_via_api_posts_to_gl(self):
        """Confirming an invoice via API posts to GL and updates balance."""
        self.client.force_authenticate(user=self.user)
        # Create invoice
        create_resp = self.client.post(reverse("invoice-list"), {
            "type": "sales",
            "date_jalali": "1404/04/01",
            "date": "2025-06-21",
            "customer": self.customer.pk,
            "subtotal": 10000000,
            "tax_amount": 1000000,
            "total": 11000000,
            "items": [{"description": "test", "quantity": 1, "unit_price": 10000000, "total": 10000000}],
        }, format="json")
        self.assertIn(create_resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(create_resp.data["success"])
        invoice_id = create_resp.data["data"]["id"]

        # Confirm
        confirm_resp = self.client.post(
            reverse("invoice-confirm", args=[invoice_id])
        )
        self.assertEqual(confirm_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(confirm_resp.data["success"])
        self.assertEqual(confirm_resp.data["data"]["status"], "confirmed")

        # Verify customer balance updated
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.balance, 11000000)

        # Verify journal voucher was created
        invoice = Invoice.objects.get(pk=invoice_id)
        self.assertIsNotNone(invoice.journal_voucher)

        # Verify journal entries are balanced
        voucher = invoice.journal_voucher
        total_debit = sum(e.debit for e in voucher.entries.all())
        total_credit = sum(e.credit for e in voucher.entries.all())
        self.assertEqual(total_debit, total_credit)

    def test_voucher_confirm_via_api(self):
        """Confirming a balanced voucher via API works."""
        self.client.force_authenticate(user=self.user)
        create_resp = self.client.post(reverse("voucher-list"), {
            "date_jalali": "1404/04/01",
            "date": "2025-06-21",
            "description": "انتقال وجه",
            "entries": [
                {"kol": self.kol_bank.pk, "debit": 5000000, "credit": 0},
                {"kol": self.kol_customer.pk, "debit": 0, "credit": 5000000},
            ],
        }, format="json")
        self.assertIn(create_resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(create_resp.data["success"])
        voucher_id = create_resp.data["data"]["id"]

        confirm_resp = self.client.post(
            reverse("voucher-confirm", args=[voucher_id])
        )
        self.assertEqual(confirm_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(confirm_resp.data["success"])
        self.assertEqual(confirm_resp.data["data"]["status"], "confirmed")
