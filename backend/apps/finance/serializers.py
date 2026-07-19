"""Finance module serializers."""

from rest_framework import serializers
from .models import (
    AccountGroup, KolAccount, MoinAccount, TafziliAccount,
    BankAccount, Customer, Supplier, FiscalYear,
    JournalVoucher, JournalEntry,
    Invoice, InvoiceItem, Receipt, Payment, Cheque,
)


# ─── Chart of Accounts ────────────────────────────────────────────

class AccountGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountGroup
        fields = ["id", "code", "name", "name_en"]


class KolAccountSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = KolAccount
        fields = ["id", "code", "name", "name_en", "group", "group_name", "account_type", "is_balance_sheet", "normal_balance", "is_active"]


class MoinAccountSerializer(serializers.ModelSerializer):
    kol_name = serializers.CharField(source="kol.name", read_only=True)

    class Meta:
        model = MoinAccount
        fields = ["id", "code", "name", "name_en", "kol", "kol_name", "is_active"]


class TafziliAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TafziliAccount
        fields = ["id", "code", "name", "name_en", "entity_type", "parent", "is_active"]


# ─── Bank & Cash ──────────────────────────────────────────────────

class BankAccountSerializer(serializers.ModelSerializer):
    tafzili_name = serializers.CharField(source="tafzili.name", read_only=True, default=None)

    class Meta:
        model = BankAccount
        fields = [
            "id", "name", "account_type", "bank_name", "branch_name",
            "account_number", "card_number", "sheba_number",
            "tafzili", "tafzili_name", "opening_balance", "current_balance", "is_active",
        ]


# ─── Customer / Supplier ─────────────────────────────────────────

class CustomerSerializer(serializers.ModelSerializer):
    tafzili_code = serializers.CharField(source="tafzili.code", read_only=True, default=None)

    class Meta:
        model = Customer
        fields = [
            "id", "tafzili", "tafzili_code", "name", "name_en",
            "national_id", "economic_code", "registration_number",
            "phone", "mobile", "email", "address", "postal_code",
            "credit_limit", "balance", "is_active",
        ]


class SupplierSerializer(serializers.ModelSerializer):
    tafzili_code = serializers.CharField(source="tafzili.code", read_only=True, default=None)

    class Meta:
        model = Supplier
        fields = [
            "id", "tafzili", "tafzili_code", "name", "name_en",
            "national_id", "economic_code", "phone", "mobile",
            "email", "address", "postal_code", "balance", "is_active",
        ]


# ─── Fiscal Year ─────────────────────────────────────────────────

class FiscalYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalYear
        fields = ["id", "name", "start_date_jalali", "end_date_jalali", "start_date", "end_date", "is_closed"]


# ─── Journal Voucher ─────────────────────────────────────────────

class JournalEntrySerializer(serializers.ModelSerializer):
    kol_name = serializers.CharField(source="kol.name", read_only=True)
    moin_name = serializers.CharField(source="moin.name", read_only=True, default=None)
    tafzili_name = serializers.CharField(source="tafzili.name", read_only=True, default=None)

    class Meta:
        model = JournalEntry
        fields = [
            "id", "kol", "kol_name", "moin", "moin_name", "tafzili", "tafzili_name",
            "description", "debit", "credit",
        ]


class JournalVoucherSerializer(serializers.ModelSerializer):
    entries = JournalEntrySerializer(many=True, read_only=True)
    total_debit = serializers.IntegerField(read_only=True)
    total_credit = serializers.IntegerField(read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True, default=None)

    class Meta:
        model = JournalVoucher
        fields = [
            "id", "number", "date_jalali", "date", "description",
            "source_type", "source_id", "status",
            "entries", "total_debit", "total_credit",
            "created_by", "created_by_name", "created_at",
        ]


class JournalVoucherCreateSerializer(serializers.ModelSerializer):
    entries = JournalEntrySerializer(many=True)

    class Meta:
        model = JournalVoucher
        fields = [
            "number", "date_jalali", "date", "description",
            "source_type", "source_id", "entries",
        ]

    def create(self, validated_data):
        entries_data = validated_data.pop("entries")
        voucher = JournalVoucher.objects.create(**validated_data)
        for entry_data in entries_data:
            JournalEntry.objects.create(voucher=voucher, **entry_data)
        return voucher


# ─── Invoice ─────────────────────────────────────────────────────

class InvoiceItemSerializer(serializers.ModelSerializer):
    kol_name = serializers.CharField(source="kol.name", read_only=True, default=None)

    class Meta:
        model = InvoiceItem
        fields = [
            "id", "description", "quantity", "unit", "unit_price",
            "discount", "tax_rate", "tax_amount", "total",
            "kol", "kol_name", "moin",
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True, default=None)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True, default=None)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True, default=None)

    class Meta:
        model = Invoice
        fields = [
            "id", "number", "type", "date_jalali", "date",
            "due_date_jalali", "due_date",
            "customer", "customer_name", "supplier", "supplier_name",
            "subtotal", "discount", "tax_rate", "tax_amount", "total",
            "description", "reference", "status",
            "items", "created_by", "created_by_name", "created_at",
        ]


class InvoiceCreateSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)

    class Meta:
        model = Invoice
        fields = [
            "number", "type", "date_jalali", "date",
            "due_date_jalali", "due_date",
            "customer", "supplier",
            "subtotal", "discount", "tax_rate", "tax_amount", "total",
            "description", "reference", "items",
        ]
        read_only_fields = ["company", "fiscal_year", "created_by"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        invoice = Invoice.objects.create(**validated_data)
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)
        return invoice


# ─── Receipt / Payment ───────────────────────────────────────────

class ReceiptSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    bank_account_name = serializers.CharField(source="bank_account.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True, default=None)

    class Meta:
        model = Receipt
        fields = [
            "id", "number", "date_jalali", "date",
            "customer", "customer_name", "bank_account", "bank_account_name",
            "amount", "payment_method", "reference", "description",
            "invoice", "status", "created_by", "created_by_name", "created_at",
        ]


class PaymentSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    bank_account_name = serializers.CharField(source="bank_account.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True, default=None)

    class Meta:
        model = Payment
        fields = [
            "id", "number", "date_jalali", "date",
            "supplier", "supplier_name", "bank_account", "bank_account_name",
            "amount", "payment_method", "reference", "description",
            "invoice", "status", "created_by", "created_by_name", "created_at",
        ]


# ─── Cheque ──────────────────────────────────────────────────────

class ChequeSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True, default=None)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True, default=None)

    class Meta:
        model = Cheque
        fields = [
            "id", "cheque_type", "number", "bank_name", "branch_name",
            "amount", "issue_date_jalali", "issue_date",
            "due_date_jalali", "due_date",
            "customer", "customer_name", "supplier", "supplier_name",
            "status", "description", "created_at",
        ]
