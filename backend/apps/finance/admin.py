from django.contrib import admin
from .models import (
    AccountGroup, KolAccount, MoinAccount, TafziliAccount,
    BankAccount, Customer, Supplier, FiscalYear,
    JournalVoucher, JournalEntry, Invoice, InvoiceItem,
    Receipt, Payment, Cheque,
)


@admin.register(AccountGroup)
class AccountGroupAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "company"]
    list_filter = ["company"]


@admin.register(KolAccount)
class KolAccountAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "group", "account_type", "company"]
    list_filter = ["company", "account_type", "group"]


@admin.register(MoinAccount)
class MoinAccountAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "kol", "company"]
    list_filter = ["company", "kol"]


@admin.register(TafziliAccount)
class TafziliAccountAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "entity_type", "company"]
    list_filter = ["company", "entity_type"]


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ["name", "account_type", "bank_name", "current_balance", "company"]
    list_filter = ["company", "account_type"]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "national_id", "balance", "company"]
    list_filter = ["company"]
    search_fields = ["name", "national_id"]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "national_id", "balance", "company"]
    list_filter = ["company"]
    search_fields = ["name", "national_id"]


@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date_jalali", "end_date_jalali", "is_closed", "company"]
    list_filter = ["company", "is_closed"]


@admin.register(JournalVoucher)
class JournalVoucherAdmin(admin.ModelAdmin):
    list_display = ["number", "date_jalali", "description", "status", "company"]
    list_filter = ["company", "status"]


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ["voucher", "kol", "moin", "tafzili", "debit", "credit"]
    list_filter = ["voucher__company"]


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["number", "type", "date_jalali", "total", "status", "company"]
    list_filter = ["company", "type", "status"]
    inlines = [InvoiceItemInline]


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ["number", "date_jalali", "customer", "amount", "payment_method", "status"]
    list_filter = ["company", "status", "payment_method"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["number", "date_jalali", "supplier", "amount", "payment_method", "status"]
    list_filter = ["company", "status", "payment_method"]


@admin.register(Cheque)
class ChequeAdmin(admin.ModelAdmin):
    list_display = ["number", "cheque_type", "bank_name", "amount", "due_date_jalali", "status"]
    list_filter = ["company", "cheque_type", "status"]
