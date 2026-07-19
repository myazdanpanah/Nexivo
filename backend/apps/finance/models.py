"""
Finance Module Models — Iranian Accounting System (Sepidar-style)

Chart of Accounts structure follows the Iranian 4-tier coding system:
  Group → Kol (General) → Moin (Subsidiary) → Tafzili (Detail)

Key conventions:
- Jalali calendar for all dates
- IRR (Rial) as base currency, Toman display option
- Tafzili-e-Shenavar (Floating Tafzili) for flexible entity tracking
- Automatic journal entry generation from invoices/receipts/payments
"""

from django.db import models
from django.conf import settings


# ─── Chart of Accounts ────────────────────────────────────────────

class AccountGroup(models.Model):
    """
    Top-level account group (1xxx Assets, 2xxx Liabilities, etc.)
    Standard Iranian accounting groups.
    """
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="account_groups")
    code = models.CharField(max_length=1, help_text="1-digit group code (1-5)")
    name = models.CharField(max_length=100, help_text="e.g. دارایی‌ها (Assets)")
    name_en = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        unique_together = [("company", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class KolAccount(models.Model):
    """
    General Ledger account (Kol / کل).
    3-digit code, e.g. 101 = صندوق (Cash), 102 = بانک (Bank)
    """
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="kol_accounts")
    group = models.ForeignKey(AccountGroup, on_delete=models.PROTECT, related_name="kol_accounts")
    code = models.CharField(max_length=3, help_text="3-digit Kol code")
    name = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True, default="")
    account_type = models.CharField(max_length=20, choices=[
        ("asset", "دارایی"),
        ("liability", "بدهی"),
        ("equity", "سرمایه"),
        ("revenue", "درآمد"),
        ("expense", "هزینه"),
    ])
    is_balance_sheet = models.BooleanField(default=True, help_text="Balance sheet or income statement?")
    normal_balance = models.CharField(max_length=10, choices=[
        ("debit", "بدهکار"),
        ("credit", "بستانکار"),
    ])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("company", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class MoinAccount(models.Model):
    """
    Subsidiary Ledger account (Moin / معین).
    4-digit code under a Kol account, e.g. 10101 = صندوق اصلی
    """
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="moin_accounts")
    kol = models.ForeignKey(KolAccount, on_delete=models.PROTECT, related_name="moin_accounts")
    code = models.CharField(max_length=4, help_text="4-digit Moin code")
    name = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("company", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class TafziliAccount(models.Model):
    """
    Detail Ledger account (Tafzili / تفصیلی).
    Most granular level — represents specific entities (customers, suppliers, bank branches).
    Supports floating tafzili (can be linked to multiple Moin accounts).
    """
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="tafzili_accounts")
    code = models.CharField(max_length=10, help_text="Tafzili code (e.g. 10001)")
    name = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True, default="")
    entity_type = models.CharField(max_length=20, choices=[
        ("customer", "مشتری"),
        ("supplier", "تأمین‌کننده"),
        ("employee", "کارمند"),
        ("bank", "شعبه بانک"),
        ("other", "سایر"),
    ], default="other")
    # Floating tafzili: linked to multiple Moin accounts
    linked_moin_accounts = models.ManyToManyField(MoinAccount, blank=True, related_name="tafzili_links")
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("company", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


# ─── Bank & Cash Management ──────────────────────────────────────

class BankAccount(models.Model):
    """Bank account / cash register."""
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="bank_accounts")
    name = models.CharField(max_length=200, help_text="e.g. حساب بانک ملت شعبه ولیعصر")
    account_type = models.CharField(max_length=20, choices=[
        ("bank", "حساب بانکی"),
        ("cash", "صندوق نقدی"),
        ("petty_cash", "تنخواه‌گردان"),
    ])
    bank_name = models.CharField(max_length=200, blank=True, default="")
    branch_name = models.CharField(max_length=200, blank=True, default="")
    account_number = models.CharField(max_length=50, blank=True, default="")
    card_number = models.CharField(max_length=20, blank=True, default="", help_text="شماره کارت")
    sheba_number = models.CharField(max_length=24, blank=True, default="", help_text="شماره شبا")
    tafzili = models.ForeignKey(TafziliAccount, on_delete=models.SET_NULL, null=True, blank=True)
    opening_balance = models.BigIntegerField(default=0, help_text="مانده اولیه (ریال)")
    current_balance = models.BigIntegerField(default=0, help_text="مانده فعلی (ریال)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# ─── Customer / Supplier ─────────────────────────────────────────

class Customer(models.Model):
    """Customer (مشتری) with Tafzili code and full contact info."""
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="finance_customers")
    tafzili = models.OneToOneField(TafziliAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name="customer")
    name = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True, default="")
    national_id = models.CharField(max_length=11, blank=True, default="", help_text="کد ملی")
    economic_code = models.CharField(max_length=12, blank=True, default="", help_text="کد اقتصادی")
    registration_number = models.CharField(max_length=20, blank=True, default="", help_text="شماره ثبت")
    phone = models.CharField(max_length=20, blank=True, default="")
    mobile = models.CharField(max_length=11, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    address = models.TextField(blank=True, default="")
    postal_code = models.CharField(max_length=10, blank=True, default="")
    credit_limit = models.BigIntegerField(default=0, help_text="سقف اعتبار (ریال)")
    balance = models.BigIntegerField(default=0, help_text="مانده حساب (ریال)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Supplier(models.Model):
    """Supplier (تأمین‌کننده / طرف حساب) with Tafzili code."""
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="finance_suppliers")
    tafzili = models.OneToOneField(TafziliAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name="supplier")
    name = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True, default="")
    national_id = models.CharField(max_length=11, blank=True, default="", help_text="کد ملی / شماره اقتصادی")
    economic_code = models.CharField(max_length=12, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    mobile = models.CharField(max_length=11, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    address = models.TextField(blank=True, default="")
    postal_code = models.CharField(max_length=10, blank=True, default="")
    balance = models.BigIntegerField(default=0, help_text="مانده حساب (ریال)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# ─── Journal Voucher (Sanad) ─────────────────────────────────────

class FiscalYear(models.Model):
    """Fiscal year (سال مالی) — Jalali calendar based."""
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="fiscal_years")
    name = models.CharField(max_length=50, help_text="e.g. ۱۴۰۴")
    start_date_jalali = models.CharField(max_length=10, help_text="YYYY/MM/DD")
    end_date_jalali = models.CharField(max_length=10, help_text="YYYY/MM/DD")
    start_date = models.DateField(help_text="Gregorian start")
    end_date = models.DateField(help_text="Gregorian end")
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("company", "name")]
        ordering = ["-name"]

    def __str__(self):
        return f"سال مالی {self.name}"


class JournalVoucher(models.Model):
    """
    Journal Voucher (سند حسابداری).
    Every financial transaction must be recorded via a numbered voucher.
    """
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="journal_vouchers")
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.PROTECT, related_name="vouchers")
    number = models.IntegerField(help_text="Sequential voucher number per fiscal year")
    date_jalali = models.CharField(max_length=10, help_text="YYYY/MM/DD")
    date = models.DateField(help_text="Gregorian date")
    description = models.CharField(max_length=500)
    source_type = models.CharField(max_length=30, choices=[
        ("manual", "دستی"),
        ("invoice", "صورتحساب"),
        ("receipt", "دریافت"),
        ("payment", "پرداخت"),
        ("opening", "مانده اولیه"),
    ], default="manual")
    source_id = models.IntegerField(null=True, blank=True, help_text="ID of the source document")
    status = models.CharField(max_length=20, choices=[
        ("draft", "پیش‌نویس"),
        ("confirmed", "تأیید شده"),
        ("cancelled", "لغو شده"),
    ], default="draft")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_vouchers")
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="confirmed_vouchers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("company", "fiscal_year", "number")]
        ordering = ["-date", "-number"]

    def __str__(self):
        return f"سند شماره {self.number} - {self.date_jalali}"

    @property
    def total_debit(self):
        return sum(e.debit for e in self.entries.all())

    @property
    def total_credit(self):
        return sum(e.credit for e in self.entries.all())


class JournalEntry(models.Model):
    """
    Journal Entry line (سطر سند حسابداری).
    Each voucher has 2+ entries: debit and credit must balance.
    """
    voucher = models.ForeignKey(JournalVoucher, on_delete=models.CASCADE, related_name="entries")
    kol = models.ForeignKey(KolAccount, on_delete=models.PROTECT, related_name="entries")
    moin = models.ForeignKey(MoinAccount, on_delete=models.PROTECT, related_name="entries", null=True, blank=True)
    tafzili = models.ForeignKey(TafziliAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name="entries")
    description = models.CharField(max_length=500, blank=True, default="")
    debit = models.BigIntegerField(default=0, help_text="بدهکار (ریال)")
    credit = models.BigIntegerField(default=0, help_text="بستانکار (ریال)")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        parts = [self.kol.name]
        if self.moin:
            parts.append(self.moin.name)
        if self.tafzili:
            parts.append(self.tafzili.name)
        return " / ".join(parts)


# ─── Invoice (Factor) ────────────────────────────────────────────

class Invoice(models.Model):
    """
    Invoice (فاکتور / صورتحساب).
    Types: Sales (فروش), Purchase (خرید), Return (برگشت).
    """
    INVOICE_TYPES = [
        ("sales", "فاکتور فروش"),
        ("purchase", "فاکتور خرید"),
        ("sales_return", "برگشت از فروش"),
        ("purchase_return", "برگشت از خرید"),
    ]

    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="invoices")
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.PROTECT, related_name="invoices")
    number = models.IntegerField(help_text="Sequential invoice number")
    type = models.CharField(max_length=20, choices=INVOICE_TYPES)
    date_jalali = models.CharField(max_length=10, help_text="YYYY/MM/DD")
    date = models.DateField()
    due_date_jalali = models.CharField(max_length=10, blank=True, default="", help_text="تاریخ سررسید")
    due_date = models.DateField(null=True, blank=True)

    # Parties
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices")

    # Amounts (in Rial)
    subtotal = models.BigIntegerField(default=0, help_text="جمع کل قبل از مالیات")
    discount = models.BigIntegerField(default=0, help_text="تخفیف")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, help_text="نرخ مالیات (%)")
    tax_amount = models.BigIntegerField(default=0, help_text="مبلغ مالیات")
    total = models.BigIntegerField(default=0, help_text="جمع کل نهایی")

    description = models.CharField(max_length=500, blank=True, default="")
    reference = models.CharField(max_length=100, blank=True, default="", help_text="مرجع / شماره قرارداد")

    # Linked journal voucher
    journal_voucher = models.ForeignKey(JournalVoucher, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices")

    status = models.CharField(max_length=20, choices=[
        ("draft", "پیش‌نویس"),
        ("confirmed", "تأیید شده"),
        ("cancelled", "لغو شده"),
    ], default="draft")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("company", "fiscal_year", "type", "number")]
        ordering = ["-date", "-number"]

    def __str__(self):
        type_label = dict(self.INVOICE_TYPES).get(self.type, self.type)
        return f"{type_label} شماره {self.number}"


class InvoiceItem(models.Model):
    """Line item of an invoice."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit = models.CharField(max_length=20, default="عدد")
    unit_price = models.BigIntegerField(default=0, help_text="قیمت واحد (ریال)")
    discount = models.BigIntegerField(default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    tax_amount = models.BigIntegerField(default=0)
    total = models.BigIntegerField(default=0, help_text="جمع ردیف")
    kol = models.ForeignKey(KolAccount, on_delete=models.SET_NULL, null=True, blank=True, help_text="حساب معین")
    moin = models.ForeignKey(MoinAccount, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.description


# ─── Receipt (Daryaft / واریزی) ──────────────────────────────────

class Receipt(models.Model):
    """
    Receipt (رسید دریافت / واریزی).
    Records money received from customers.
    """
    PAYMENT_METHODS = [
        ("cash", "نقدی"),
        ("bank_transfer", "انتقال بانکی"),
        ("cheque", "چک"),
        ("pos", "دستگاه کارت خوان"),
        ("online", "پرداخت آنلاین"),
    ]

    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="receipts")
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.PROTECT, related_name="receipts")
    number = models.IntegerField()
    date_jalali = models.CharField(max_length=10)
    date = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="receipts")
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name="receipts")
    amount = models.BigIntegerField(help_text="مبلغ (ریال)")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=100, blank=True, default="", help_text="شماره چک / پیگیری")
    description = models.CharField(max_length=500, blank=True, default="")
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name="receipts")
    journal_voucher = models.ForeignKey(JournalVoucher, on_delete=models.SET_NULL, null=True, blank=True, related_name="receipts")
    status = models.CharField(max_length=20, choices=[
        ("draft", "پیش‌نویس"),
        ("confirmed", "تأیید شده"),
        ("cancelled", "لغو شده"),
    ], default="draft")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("company", "fiscal_year", "number")]
        ordering = ["-date", "-number"]

    def __str__(self):
        return f"رسید شماره {self.number} - {self.date_jalali}"


# ─── Payment (Pardakht / پرداختی) ────────────────────────────────

class Payment(models.Model):
    """
    Payment (پرداختی).
    Records money paid to suppliers.
    """
    PAYMENT_METHODS = [
        ("cash", "نقدی"),
        ("bank_transfer", "انتقال بانکی"),
        ("cheque", "چک"),
        ("pos", "دستگاه کارت خوان"),
    ]

    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="payments")
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.PROTECT, related_name="payments")
    number = models.IntegerField()
    date_jalali = models.CharField(max_length=10)
    date = models.DateField()
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="payments")
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name="payments")
    amount = models.BigIntegerField(help_text="مبلغ (ریال)")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=100, blank=True, default="", help_text="شماره چک / پیگیری")
    description = models.CharField(max_length=500, blank=True, default="")
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    journal_voucher = models.ForeignKey(JournalVoucher, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    status = models.CharField(max_length=20, choices=[
        ("draft", "پیش‌نویس"),
        ("confirmed", "تأیید شده"),
        ("cancelled", "لغو شده"),
    ], default="draft")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("company", "fiscal_year", "number")]
        ordering = ["-date", "-number"]

    def __str__(self):
        return f"پرداخت شماره {self.number} - {self.date_jalali}"


# ─── Cheque Management ──────────────────────────────────────────

class Cheque(models.Model):
    """
    Cheque (چک) — both received and issued.
    """
    CHEQUE_TYPES = [
        ("received", "دریافتی"),
        ("issued", "صادره"),
    ]
    CHEQUE_STATUS = [
        ("pending", "در انتظار"),
        ("passed", "وصول شده"),
        ("bounced", "برگشتی"),
        ("cancelled", "لغو شده"),
    ]

    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE, related_name="cheques")
    cheque_type = models.CharField(max_length=10, choices=CHEQUE_TYPES)
    number = models.CharField(max_length=20, help_text="شماره چک")
    bank_name = models.CharField(max_length=200)
    branch_name = models.CharField(max_length=200, blank=True, default="")
    amount = models.BigIntegerField(help_text="مبلغ چک (ریال)")
    issue_date_jalali = models.CharField(max_length=10)
    issue_date = models.DateField()
    due_date_jalali = models.CharField(max_length=10, help_text="تاریخ سررسید")
    due_date = models.DateField()
    # Parties
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="cheques")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="cheques")
    status = models.CharField(max_length=20, choices=CHEQUE_STATUS, default="pending")
    description = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        type_label = "دریافتی" if self.cheque_type == "received" else "صادره"
        return f"چک {type_label} شماره {self.number} - {self.bank_name}"
