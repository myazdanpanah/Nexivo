"""
Tax Engine Tests — per TAX_AND_LEGAL_RULES_IRAN.md §19.

Tests cover:
- TaxCategory/TaxCode/TaxRule CRUD
- TaxEngine.calculate_vat (output VAT for sales invoices)
- TaxEngine.calculate_withholding_tax
- TaxEngine.get_vat_summary
- Fiscal year validation (no open fiscal year → ValidationError)
- Zero tax rules → returns zero
- Idempotency (multiple calculations create separate records)
"""

import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.tests_helpers import create_test_company, create_test_user
from apps.finance.exceptions import ValidationError
from apps.finance.models import (
    AccountGroup, KolAccount, FiscalYear,
    TaxCategory, TaxCode, TaxRule, TaxTransaction,
)
from apps.finance.tax import TaxEngine

User = get_user_model()


class TaxEngineTests(TestCase):
    """Tests for TaxEngine VAT and withholding tax calculations."""

    def setUp(self):
        self.company = create_test_company(name="TaxTestCo")
        self.user = create_test_user(username="taxuser", company=self.company, role="ceo")
        self.fy = FiscalYear.objects.create(
            company=self.company, name="1404",
            start_date_jalali="1403/01/01", end_date_jalali="1404/01/01",
            start_date=datetime.date(2024, 3, 20),
            end_date=datetime.date(2025, 3, 19),
        )
        # Chart of accounts needed for posting engine
        self.ga = AccountGroup.objects.create(company=self.company, code="1", name="Assets")
        self.gr = AccountGroup.objects.create(company=self.company, code="4", name="Revenue")
        self.kol_102 = KolAccount.objects.create(
            company=self.company, group=self.ga, code="102",
            name="Bank", account_type="asset", normal_balance="debit",
        )
        self.kol_401 = KolAccount.objects.create(
            company=self.company, group=self.gr, code="401",
            name="Sales Revenue", account_type="revenue", normal_balance="credit",
            is_balance_sheet=False,
        )
        # Tax master data
        self.taxable_cat = TaxCategory.objects.create(
            company=self.company, code="TAXABLE", name="مشمول مالیات",
        )
        self.vat_code = TaxCode.objects.create(
            company=self.company, category=self.taxable_cat,
            code="VAT_NORMAL", name="مالیات بر ارزش افزوده عادی",
            rate=Decimal("10.00"),
            effective_date=datetime.date(2024, 3, 20),
        )
        self.vat_rule = TaxRule.objects.create(
            company=self.company, name="VAT on Sales",
            tax_code=self.vat_code,
            conditions={"document_type": "sales_invoice", "item_category": "TAXABLE"},
            priority=10,
        )
        # Withholding tax rule for tests
        self.wh_code = TaxCode.objects.create(
            company=self.company, category=self.taxable_cat,
            code="WH_SERVICE", name="مالیات کسرکننده خدمات",
            rate=Decimal("5.00"),
            effective_date=datetime.date(2024, 3, 20),
        )
        self.wh_rule = TaxRule.objects.create(
            company=self.company, name="WH on Services",
            tax_code=self.wh_code,
            conditions={"document_type": "withholding", "item_category": "consulting"},
            priority=5,
        )

    def test_calculate_vat_creates_transaction(self):
        """VAT calculation records a TaxTransaction with correct amounts."""
        result = TaxEngine.calculate_vat(
            company=self.company,
            base_amount=1_000_000,
            document_type="sales_invoice",
            user=self.user,
            source_type="invoice",
            source_id=1,
            fiscal_year=self.fy,
        )
        self.assertEqual(result["tax_amount"], 100_000)
        self.assertEqual(result["tax_rate"], Decimal("10.00"))
        self.assertEqual(result["tax_code"], "VAT_NORMAL")
        self.assertIsNotNone(result["transaction_id"])

        tx = TaxTransaction.objects.get(id=result["transaction_id"])
        self.assertEqual(tx.company, self.company)
        self.assertEqual(tx.fiscal_year, self.fy)
        self.assertEqual(tx.base_amount, 1_000_000)
        self.assertEqual(tx.tax_amount, 100_000)
        self.assertEqual(tx.vat_type, "output")
        self.assertEqual(tx.status, "calculated")

    def test_calculate_vat_output_for_sales(self):
        """Sales invoices produce output VAT."""
        result = TaxEngine.calculate_vat(
            company=self.company, base_amount=500_000,
            document_type="sales_invoice", user=self.user,
            fiscal_year=self.fy,
        )
        tx = TaxTransaction.objects.get(id=result["transaction_id"])
        self.assertEqual(tx.vat_type, "output")

    def test_calculate_vat_input_for_purchase(self):
        """Purchase invoices produce input VAT."""
        # Add a purchase rule for this test
        TaxRule.objects.create(
            company=self.company, name="VAT on Purchases",
            tax_code=self.vat_code,
            conditions={"document_type": "purchase_invoice", "item_category": "TAXABLE"},
            priority=10,
        )
        result = TaxEngine.calculate_vat(
            company=self.company, base_amount=2_000_000,
            document_type="purchase_invoice", user=self.user,
            fiscal_year=self.fy,
        )
        tx = TaxTransaction.objects.get(id=result["transaction_id"])
        self.assertEqual(tx.vat_type, "input")

    def test_calculate_vat_no_rules_returns_zero(self):
        """When no matching tax rules exist, returns zero tax."""
        result = TaxEngine.calculate_vat(
            company=self.company, base_amount=1_000_000,
            document_type="import", user=self.user,
            fiscal_year=self.fy,
        )
        self.assertEqual(result["tax_amount"], 0)
        self.assertIsNone(result["tax_code"])
        self.assertIsNone(result["transaction_id"])

    def test_calculate_vat_no_fiscal_year_raises(self):
        """Missing fiscal year raises ValidationError."""
        # Close all fiscal years
        self.fy.is_closed = True
        self.fy.save()
        with self.assertRaises(ValidationError) as ctx:
            TaxEngine.calculate_vat(
                company=self.company, base_amount=1_000_000,
                document_type="sales_invoice", user=self.user,
            )
        self.assertIn("fiscal year", str(ctx.exception).lower())

    def test_calculate_vat_auto_lookup_fiscal_year(self):
        """When fiscal_year=None and an open FY exists, auto-lookup succeeds."""
        result = TaxEngine.calculate_vat(
            company=self.company, base_amount=1_000_000,
            document_type="sales_invoice", user=self.user,
            source_id=42,
            # fiscal_year intentionally omitted (None)
        )
        self.assertEqual(result["tax_amount"], 100_000)
        self.assertIsNotNone(result["transaction_id"])
        tx = TaxTransaction.objects.get(id=result["transaction_id"])
        self.assertEqual(tx.fiscal_year, self.fy)
        self.assertEqual(tx.source_id, 42)
        self.assertEqual(tx.vat_type, "output")

    def test_withholding_tax_auto_lookup_fiscal_year(self):
        """When fiscal_year=None and an open FY exists, withholding auto-lookup succeeds."""
        result = TaxEngine.calculate_withholding_tax(
            company=self.company, base_amount=2_000_000,
            service_type="consulting", user=self.user,
            # fiscal_year intentionally omitted (None)
        )
        self.assertEqual(result["tax_amount"], 100_000)
        tx = TaxTransaction.objects.get(id=result["transaction_id"])
        self.assertEqual(tx.fiscal_year, self.fy)

    def test_calculate_vat_idempotency(self):
        """Multiple VAT calculations create separate transactions."""
        for i in range(3):
            TaxEngine.calculate_vat(
                company=self.company, base_amount=100_000 * (i + 1),
                document_type="sales_invoice", user=self.user,
                source_id=i + 1, fiscal_year=self.fy,
            )
        self.assertEqual(TaxTransaction.objects.count(), 3)

    def test_withholding_tax_creates_transaction(self):
        """Withholding tax calculation works correctly."""
        result = TaxEngine.calculate_withholding_tax(
            company=self.company, base_amount=4_000_000,
            service_type="consulting", user=self.user,
            source_type="payment", source_id=1,
            fiscal_year=self.fy,
        )
        self.assertEqual(result["tax_amount"], 200_000)
        self.assertEqual(result["tax_rate"], Decimal("5.00"))
        self.assertIsNotNone(result["transaction_id"])

    def test_withholding_tax_no_rules_returns_zero(self):
        """No withholding rules → zero tax."""
        result = TaxEngine.calculate_withholding_tax(
            company=self.company, base_amount=1_000_000,
            service_type="unknown", user=self.user,
            fiscal_year=self.fy,
        )
        self.assertEqual(result["tax_amount"], 0)
        self.assertIsNone(result["transaction_id"])

    def test_withholding_tax_no_fiscal_year_raises(self):
        """Missing fiscal year raises ValidationError."""
        self.fy.is_closed = True
        self.fy.save()
        with self.assertRaises(ValidationError):
            TaxEngine.calculate_withholding_tax(
                company=self.company, base_amount=1_000_000,
                service_type="consulting", user=self.user,
            )

    def test_get_vat_summary(self):
        """VAT summary correctly aggregates output/input VAT."""
        # Create output VAT transaction (posted)
        TaxTransaction.objects.create(
            company=self.company, fiscal_year=self.fy,
            tax_code=self.vat_code, tax_rule=self.vat_rule,
            source_type="invoice", source_id=1,
            base_amount=10_000_000, tax_amount=1_000_000,
            tax_rate=Decimal("10.00"), vat_type="output",
            status="posted", created_by=self.user,
        )
        # Create input VAT transaction (posted)
        TaxTransaction.objects.create(
            company=self.company, fiscal_year=self.fy,
            tax_code=self.vat_code, tax_rule=self.vat_rule,
            source_type="invoice", source_id=2,
            base_amount=5_000_000, tax_amount=500_000,
            tax_rate=Decimal("10.00"), vat_type="input",
            status="posted", created_by=self.user,
        )
        # Unposted transaction (should not be counted)
        TaxTransaction.objects.create(
            company=self.company, fiscal_year=self.fy,
            tax_code=self.vat_code, tax_rule=self.vat_rule,
            source_type="invoice", source_id=3,
            base_amount=2_000_000, tax_amount=200_000,
            tax_rate=Decimal("10.00"), vat_type="output",
            status="calculated", created_by=self.user,
        )

        summary = TaxEngine.get_vat_summary(self.company)
        self.assertEqual(summary["output_vat"], 1_000_000)
        self.assertEqual(summary["input_vat"], 500_000)
        self.assertEqual(summary["vat_payable"], 500_000)
        self.assertFalse(summary["is_settled"])

    def test_get_vat_summary_settled(self):
        """VAT is settled when input ≥ output."""
        TaxTransaction.objects.create(
            company=self.company, fiscal_year=self.fy,
            tax_code=self.vat_code, tax_rule=self.vat_rule,
            source_type="invoice", source_id=1,
            base_amount=5_000_000, tax_amount=500_000,
            tax_rate=Decimal("10.00"), vat_type="output",
            status="posted", created_by=self.user,
        )
        TaxTransaction.objects.create(
            company=self.company, fiscal_year=self.fy,
            tax_code=self.vat_code, tax_rule=self.vat_rule,
            source_type="invoice", source_id=2,
            base_amount=8_000_000, tax_amount=800_000,
            tax_rate=Decimal("10.00"), vat_type="input",
            status="posted", created_by=self.user,
        )
        summary = TaxEngine.get_vat_summary(self.company)
        self.assertTrue(summary["is_settled"])

    def test_get_vat_summary_filtered_by_fiscal_year(self):
        """VAT summary can be filtered by fiscal year ID."""
        TaxTransaction.objects.create(
            company=self.company, fiscal_year=self.fy,
            tax_code=self.vat_code, tax_rule=self.vat_rule,
            source_type="invoice", source_id=1,
            base_amount=3_000_000, tax_amount=300_000,
            tax_rate=Decimal("10.00"), vat_type="output",
            status="posted", created_by=self.user,
        )
        summary = TaxEngine.get_vat_summary(
            self.company, fiscal_year_id=self.fy.id
        )
        self.assertEqual(summary["output_vat"], 300_000)

    def test_get_applicable_rules_matching(self):
        """Rules are matched by document_type and item_category."""
        rules = TaxEngine.get_applicable_rules(
            self.company, "sales_invoice", "TAXABLE"
        )
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].id, self.vat_rule.id)

    def test_get_applicable_rules_no_match(self):
        """Non-matching conditions return empty list."""
        rules = TaxEngine.get_applicable_rules(
            self.company, "sales_invoice", "EXEMPT"
        )
        self.assertEqual(len(rules), 0)

    def test_get_applicable_rules_inactive_excluded(self):
        """Inactive rules are excluded."""
        self.vat_rule.is_active = False
        self.vat_rule.save()
        rules = TaxEngine.get_applicable_rules(
            self.company, "sales_invoice", "TAXABLE"
        )
        self.assertEqual(len(rules), 0)

    def test_priority_ordering(self):
        """Higher priority rule is selected first."""
        low_priority = TaxRule.objects.create(
            company=self.company, name="Low Priority VAT",
            tax_code=self.vat_code,
            conditions={"document_type": "sales_invoice", "item_category": "TAXABLE"},
            priority=1,
        )
        rules = TaxEngine.get_applicable_rules(
            self.company, "sales_invoice", "TAXABLE"
        )
        self.assertEqual(len(rules), 2)
        # Highest priority first (10 > 1)
        self.assertEqual(rules[0].name, "VAT on Sales")
