"""
Seed default Iranian chart of accounts for all companies.

Usage:
    python manage.py seed_default_accounts

Creates the 5 standard Iranian account groups (1-5) and common Kol accounts.
Idempotent — skips if groups already exist for a company.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounts.models import Company
from apps.finance.models import AccountGroup, KolAccount

# ─── Standard Iranian Account Groups ────────────────────────────
GROUPS = [
    {"code": "1", "name": "دارایی‌ها", "name_en": "Assets"},
    {"code": "2", "name": "بدهی‌ها", "name_en": "Liabilities"},
    {"code": "3", "name": "سرمایه", "name_en": "Equity"},
    {"code": "4", "name": "درآمدها", "name_en": "Revenue"},
    {"code": "5", "name": "هزینه‌ها", "name_en": "Expenses"},
]

# ─── Standard Kol Accounts per Group ────────────────────────────
KOL_ACCOUNTS = [
    # Group 1: Assets
    {"group": "1", "code": "101", "name": "صندوق", "name_en": "Cash", "account_type": "asset", "normal_balance": "debit", "is_balance_sheet": True},
    {"group": "1", "code": "102", "name": "بانک", "name_en": "Bank", "account_type": "asset", "normal_balance": "debit", "is_balance_sheet": True},
    {"group": "1", "code": "103", "name": "صندوق تنخواه‌گردان", "name_en": "Petty Cash", "account_type": "asset", "normal_balance": "debit", "is_balance_sheet": True},
    {"group": "1", "code": "104", "name": "حساب‌های دریافتنی", "name_en": "Accounts Receivable", "account_type": "asset", "normal_balance": "debit", "is_balance_sheet": True},
    {"group": "1", "code": "105", "name": "اسناد دریافتنی", "name_en": "Notes Receivable", "account_type": "asset", "normal_balance": "debit", "is_balance_sheet": True},
    {"group": "1", "code": "106", "name": "موجودی کالا", "name_en": "Inventory", "account_type": "asset", "normal_balance": "debit", "is_balance_sheet": True},
    {"group": "1", "code": "107", "name": "املاک و تجهیزات", "name_en": "Fixed Assets", "account_type": "asset", "normal_balance": "debit", "is_balance_sheet": True},
    {"group": "1", "code": "108", "name": "استهلاک انباشته", "name_en": "Accumulated Depreciation", "account_type": "asset", "normal_balance": "credit", "is_balance_sheet": True},
    # Group 2: Liabilities
    {"group": "2", "code": "201", "name": "حساب‌های پرداختنی", "name_en": "Accounts Payable", "account_type": "liability", "normal_balance": "credit", "is_balance_sheet": True},
    {"group": "2", "code": "202", "name": "اسناد پرداختنی", "name_en": "Notes Payable", "account_type": "liability", "normal_balance": "credit", "is_balance_sheet": True},
    {"group": "2", "code": "203", "name": "ذخیره مالیات", "name_en": "Tax Provision", "account_type": "liability", "normal_balance": "credit", "is_balance_sheet": True},
    {"group": "2", "code": "204", "name": "حقوق و مزایای پرداختنی", "name_en": "Salaries Payable", "account_type": "liability", "normal_balance": "credit", "is_balance_sheet": True},
    {"group": "2", "code": "205", "name": "بیمه پرداختنی", "name_en": "Insurance Payable", "account_type": "liability", "normal_balance": "credit", "is_balance_sheet": True},
    # Group 3: Equity
    {"group": "3", "code": "301", "name": "سرمایه", "name_en": "Capital", "account_type": "equity", "normal_balance": "credit", "is_balance_sheet": True},
    {"group": "3", "code": "302", "name": "سود (زیان) انباشته", "name_en": "Retained Earnings", "account_type": "equity", "normal_balance": "credit", "is_balance_sheet": True},
    {"group": "3", "code": "303", "name": "سایر اندوخته‌ها", "name_en": "Other Reserves", "account_type": "equity", "normal_balance": "credit", "is_balance_sheet": True},
    # Group 4: Revenue
    {"group": "4", "code": "401", "name": "فروش", "name_en": "Sales Revenue", "account_type": "revenue", "normal_balance": "credit", "is_balance_sheet": False},
    {"group": "4", "code": "402", "name": "درآمد خدمات", "name_en": "Service Revenue", "account_type": "revenue", "normal_balance": "credit", "is_balance_sheet": False},
    {"group": "4", "code": "403", "name": "برگشت از فروش", "name_en": "Sales Returns", "account_type": "revenue", "normal_balance": "debit", "is_balance_sheet": False},
    {"group": "4", "code": "404", "name": "تخفیفات دریافتی", "name_en": "Discounts Received", "account_type": "revenue", "normal_balance": "credit", "is_balance_sheet": False},
    # Group 5: Expenses
    {"group": "5", "code": "501", "name": "بهای تمام شده کالای فروش رفته", "name_en": "COGS", "account_type": "expense", "normal_balance": "debit", "is_balance_sheet": False},
    {"group": "5", "code": "502", "name": "هزینه حقوق و دستمزد", "name_en": "Salaries Expense", "account_type": "expense", "normal_balance": "debit", "is_balance_sheet": False},
    {"group": "5", "code": "503", "name": "هزینه اجاره", "name_en": "Rent Expense", "account_type": "expense", "normal_balance": "debit", "is_balance_sheet": False},
    {"group": "5", "code": "504", "name": "هزینه آب و برق و گاز", "name_en": "Utilities Expense", "account_type": "expense", "normal_balance": "debit", "is_balance_sheet": False},
    {"group": "5", "code": "505", "name": "هزینه استهلاک", "name_en": "Depreciation Expense", "account_type": "expense", "normal_balance": "debit", "is_balance_sheet": False},
    {"group": "5", "code": "506", "name": "هزینه بیمه", "name_en": "Insurance Expense", "account_type": "expense", "normal_balance": "debit", "is_balance_sheet": False},
    {"group": "5", "code": "507", "name": "هزینه تبلیغات", "name_en": "Advertising Expense", "account_type": "expense", "normal_balance": "debit", "is_balance_sheet": False},
    {"group": "5", "code": "508", "name": "هزینه‌های مالی (بازرگانی)", "name_en": "Financial Expense", "account_type": "expense", "normal_balance": "debit", "is_balance_sheet": False},
    {"group": "5", "code": "509", "name": "هزینه سایر", "name_en": "Other Expenses", "account_type": "expense", "normal_balance": "debit", "is_balance_sheet": False},
]


class Command(BaseCommand):
    help = "Seed default Iranian chart of accounts (groups + Kol) for all companies"

    def handle(self, *args, **options):
        companies = Company.objects.all()
        total_groups = 0
        total_kols = 0

        for company in companies:
            # Check if already seeded
            if AccountGroup.objects.filter(company=company).exists():
                self.stdout.write(f"  ⏭ {company.name}: already seeded, skipping")
                continue

            self.stdout.write(f"  📦 {company.name}: seeding...")

            with transaction.atomic():
                # Create groups
                group_map = {}
                for g in GROUPS:
                    obj, created = AccountGroup.objects.get_or_create(
                        company=company, code=g["code"],
                        defaults={"name": g["name"], "name_en": g["name_en"]},
                    )
                    group_map[g["code"]] = obj
                    if created:
                        total_groups += 1

                # Create Kol accounts
                for k in KOL_ACCOUNTS:
                    group = group_map.get(k["group"])
                    if not group:
                        continue
                    obj, created = KolAccount.objects.get_or_create(
                        company=company, code=k["code"],
                        defaults={
                            "group": group,
                            "name": k["name"],
                            "name_en": k["name_en"],
                            "account_type": k["account_type"],
                            "normal_balance": k["normal_balance"],
                            "is_balance_sheet": k["is_balance_sheet"],
                        },
                    )
                    if created:
                        total_kols += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Done! Created {total_groups} groups and {total_kols} Kol accounts across {companies.count()} companies."
        ))
