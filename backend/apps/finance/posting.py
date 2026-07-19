"""
Accounting Posting Engine — Enterprise ERP Core.

Per ACCOUNTING_MODULE.md §8: No module is allowed to directly insert journal records.
Only the Posting Engine may create journal entries.

Per ACCOUNTING_MODULE.md §2: Business Transaction → Transaction Engine → Accounting Posting Engine → Journal Entry → General Ledger → Financial Reports.

Per DJANGO_BACKEND.md §10: Services handle all business rules.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.db.models import Sum, Q, F
from django.utils import timezone

from .models import (
    KolAccount, MoinAccount, TafziliAccount,
    JournalVoucher, JournalEntry,
    FiscalYear, Customer, Supplier, BankAccount,
    Invoice, InvoiceItem, Receipt, Payment,
)
from .exceptions import ValidationError

logger = logging.getLogger(__name__)


class PostingEngine:
    """
    Central accounting posting engine.
    
    All modules create accounting entries through the Posting Engine.
    No module may directly insert journal records.
    
    Per ACCOUNTING_MODULE.md §8: Posting Rule architecture.
    """

    @staticmethod
    def _get_kol_account(company, code: str) -> KolAccount:
        """Safely get a Kol account, raising ValidationError if not found."""
        kol = KolAccount.objects.filter(company=company, code=code).first()
        if not kol:
            raise ValidationError(
                f"حساب کل با کد '{code}' در سرفصل حساب‌ها یافت نشد. "
                f"لطفاً ابتدا سرفصل حساب‌ها را تکمیل کنید."
            )
        return kol

    @staticmethod
    def _next_voucher_number(company, fiscal_year_id: int) -> int:
        """Calculate next sequential voucher number per fiscal year."""
        last = JournalVoucher.objects.filter(
            company=company, fiscal_year_id=fiscal_year_id
        ).order_by("-number").first()
        return (last.number + 1) if last else 1

    @staticmethod
    def get_open_fiscal_year(company):
        """Get the current open fiscal year."""
        return FiscalYear.objects.filter(company=company, is_closed=False).first()

    @staticmethod
    @transaction.atomic
    def post_invoice(invoice: Invoice, user: Any) -> JournalVoucher:
        """
        Post an invoice to the general ledger.
        
        Sales Invoice:
            Debit: Accounts Receivable (Customer)
            Credit: Sales Revenue
            Credit: VAT Payable
            
        Purchase Invoice:
            Debit: Inventory / Expense
            Debit: Input VAT
            Credit: Accounts Payable (Supplier)
            
        Per ACCOUNTING_MODULE.md §9: Sales Accounting.
        """
        if invoice.journal_voucher:
            return invoice.journal_voucher  # Already posted (idempotent)

        company = invoice.company
        fy = PostingEngine.get_open_fiscal_year(company)
        if not fy:
            raise ValidationError("No open fiscal year found.")

        entries = []

        if invoice.type == "sales":
            # Debit: Customer Receivable (131)
            customer_tafzili = invoice.customer.tafzili if invoice.customer else None
            entries.append({
                "kol": PostingEngine._get_kol_account(company, "131"),
                "tafzili": customer_tafzili,
                "description": f"فاکتور فروش شماره {invoice.number}",
                "debit": invoice.total,
                "credit": 0,
            })
            # Credit: Sales Revenue (401)
            entries.append({
                "kol": PostingEngine._get_kol_account(company, "401"),
                "description": f"درآمد فروش فاکتور {invoice.number}",
                "debit": 0,
                "credit": invoice.subtotal,
            })
            # Credit: VAT Payable (341)
            if invoice.tax_amount > 0:
                entries.append({
                    "kol": PostingEngine._get_kol_account(company, "341"),
                    "description": f"مالیات بر ارزش افزوده فاکتور {invoice.number}",
                    "debit": 0,
                    "credit": invoice.tax_amount,
                })
        elif invoice.type == "purchase":
            # Debit: Inventory / Expense (111)
            entries.append({
                "kol": PostingEngine._get_kol_account(company, "111"),
                "description": f"خرید فاکتور شماره {invoice.number}",
                "debit": invoice.subtotal,
                "credit": 0,
            })
            # Debit: Input VAT (133)
            if invoice.tax_amount > 0:
                entries.append({
                    "kol": PostingEngine._get_kol_account(company, "133"),
                    "description": f"مالیات پرداختی فاکتور {invoice.number}",
                    "debit": invoice.tax_amount,
                    "credit": 0,
                })
            # Credit: Supplier Payable (231)
            supplier_tafzili = invoice.supplier.tafzili if invoice.supplier else None
            entries.append({
                "kol": PostingEngine._get_kol_account(company, "231"),
                "tafzili": supplier_tafzili,
                "description": f"بدهی به تأمین‌کننده فاکتور {invoice.number}",
                "debit": 0,
                "credit": invoice.total,
            })

        if not entries:
            return None

        # Create voucher
        voucher = JournalVoucher.objects.create(
            company=company,
            fiscal_year=fy,
            number=PostingEngine._next_voucher_number(company, fy.id),
            date_jalali=invoice.date_jalali,
            date=invoice.date,
            description=f"سند صورتحساب {invoice.number}",
            source_type="invoice",
            source_id=invoice.id,
            status="confirmed",
            created_by=user,
            confirmed_by=user,
        )

        # Create journal entries — each must reference a Kol account
        for entry_data in entries:
            kol = entry_data.pop("kol", None)
            moin = entry_data.pop("moin", None)
            tafzili = entry_data.pop("tafzili", None)
            JournalEntry.objects.create(
                voucher=voucher,
                kol=kol,
                moin=moin,
                tafzili=tafzili,
                **entry_data,
            )

        # Link voucher to invoice
        invoice.journal_voucher = voucher
        invoice.save(update_fields=["journal_voucher"])

        logger.info(f"Invoice #{invoice.number} posted as voucher #{voucher.number}")
        return voucher

    @staticmethod
    @transaction.atomic
    def post_receipt(receipt: Receipt, user: Any) -> JournalVoucher:
        """
        Post a receipt to the general ledger.
        
        Receipt:
            Debit: Bank / Cash
            Credit: Customer Receivable
            
        Per ACCOUNTING_MODULE.md §15: Treasury Module Integration.
        """
        if receipt.journal_voucher:
            return receipt.journal_voucher

        company = receipt.company
        fy = PostingEngine.get_open_fiscal_year(company)
        if not fy:
            raise ValidationError("No open fiscal year found.")

        voucher = JournalVoucher.objects.create(
            company=company,
            fiscal_year=fy,
            number=PostingEngine._next_voucher_number(company, fy.id),
            date_jalali=receipt.date_jalali,
            date=receipt.date,
            description=f"رسید دریافت شماره {receipt.number}",
            source_type="receipt",
            source_id=receipt.id,
            status="confirmed",
            created_by=user,
            confirmed_by=user,
        )

        # Debit: Bank / Cash (use bank account's tafzili if available)
        bank_tafzili = receipt.bank_account.tafzili if receipt.bank_account else None
        JournalEntry.objects.create(
            voucher=voucher,
            kol=PostingEngine._get_kol_account(company, "102"),  # Bank Kol
            tafzili=bank_tafzili,
            description=f"واریز به حساب بانکی - رسید {receipt.number}",
            debit=receipt.amount,
            credit=0,
        )
        # Credit: Customer Receivable (use customer's tafzili if available)
        customer_tafzili = receipt.customer.tafzili if receipt.customer else None
        JournalEntry.objects.create(
            voucher=voucher,
            kol=PostingEngine._get_kol_account(company, "131"),  # Customer Receivable Kol
            tafzili=customer_tafzili,
            description=f"دریافت از مشتری - رسید {receipt.number}",
            debit=0,
            credit=receipt.amount,
        )

        receipt.journal_voucher = voucher
        receipt.save(update_fields=["journal_voucher"])

        logger.info(f"Receipt #{receipt.number} posted as voucher #{voucher.number}")
        return voucher

    @staticmethod
    @transaction.atomic
    def post_payment(payment: Payment, user: Any) -> JournalVoucher:
        """
        Post a payment to the general ledger.
        
        Payment:
            Debit: Supplier Payable
            Credit: Bank / Cash
            
        Per ACCOUNTING_MODULE.md §15: Treasury Module Integration.
        """
        if payment.journal_voucher:
            return payment.journal_voucher

        company = payment.company
        fy = PostingEngine.get_open_fiscal_year(company)
        if not fy:
            raise ValidationError("No open fiscal year found.")

        voucher = JournalVoucher.objects.create(
            company=company,
            fiscal_year=fy,
            number=PostingEngine._next_voucher_number(company, fy.id),
            date_jalali=payment.date_jalali,
            date=payment.date,
            description=f"پرداخت شماره {payment.number}",
            source_type="payment",
            source_id=payment.id,
            status="confirmed",
            created_by=user,
            confirmed_by=user,
        )

        # Debit: Supplier Payable (use supplier's tafzili if available)
        supplier_tafzili = payment.supplier.tafzili if payment.supplier else None
        JournalEntry.objects.create(
            voucher=voucher,
            kol=PostingEngine._get_kol_account(company, "231"),  # Supplier Payable Kol
            tafzili=supplier_tafzili,
            description=f"پرداخت به تأمین‌کننده - پرداختی {payment.number}",
            debit=payment.amount,
            credit=0,
        )
        # Credit: Bank / Cash (use bank account's tafzili if available)
        bank_tafzili = payment.bank_account.tafzili if payment.bank_account else None
        JournalEntry.objects.create(
            voucher=voucher,
            kol=PostingEngine._get_kol_account(company, "102"),  # Bank Kol
            tafzili=bank_tafzili,
            description=f"برداشت از حساب بانکی - پرداختی {payment.number}",
            debit=0,
            credit=payment.amount,
        )

        payment.journal_voucher = voucher
        payment.save(update_fields=["journal_voucher"])

        logger.info(f"Payment #{payment.number} posted as voucher #{voucher.number}")
        return voucher


class LedgerService:
    """
    Read-only ledger queries for financial statements.
    
    Per ACCOUNTING_MODULE.md §18: Financial Reports.
    Per REPORT_ENGINE.md: Read-optimized queries.
    """

    @staticmethod
    def get_trial_balance(company, fiscal_year_id: Optional[int] = None) -> List[Dict]:
        """
        Generate trial balance — total debits and credits per account.
        All accounts must balance (total debit == total credit).
        """
        fy_filter = {"fiscal_year_id": fiscal_year_id} if fiscal_year_id else {}
        vouchers = JournalVoucher.objects.filter(
            company=company, status="confirmed", **fy_filter
        )
        entries = JournalEntry.objects.filter(voucher__in=vouchers)

        account_totals = {}
        for entry in entries.select_related("kol"):
            kol_id = entry.kol_id
            if kol_id not in account_totals:
                account_totals[kol_id] = {
                    "kol_id": kol_id,
                    "kol_name": entry.kol.name,
                    "kol_code": entry.kol.code,
                    "account_type": entry.kol.account_type,
                    "total_debit": 0,
                    "total_credit": 0,
                }
            account_totals[kol_id]["total_debit"] += entry.debit
            account_totals[kol_id]["total_credit"] += entry.credit

        result = list(account_totals.values())
        total_debit = sum(r["total_debit"] for r in result)
        total_credit = sum(r["total_credit"] for r in result)

        return {
            "accounts": result,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "is_balanced": total_debit == total_credit,
        }

    @staticmethod
    def get_account_balance(company, kol_id: int, fiscal_year_id: Optional[int] = None) -> Dict:
        """Get the balance of a specific account."""
        fy_filter = {"fiscal_year_id": fiscal_year_id} if fiscal_year_id else {}
        totals = JournalEntry.objects.filter(
            voucher__company=company,
            voucher__status="confirmed",
            kol_id=kol_id,
            **fy_filter,
        ).aggregate(
            total_debit=Sum("debit"),
            total_credit=Sum("credit"),
        )

        total_debit = totals["total_debit"] or 0
        total_credit = totals["total_credit"] or 0
        balance = total_debit - total_credit

        return {
            "kol_id": kol_id,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "balance": balance,
        }

    @staticmethod
    def get_customer_ledger(company, customer_id: int) -> List[Dict]:
        """Get all journal entries related to a specific customer."""
        entries = JournalEntry.objects.filter(
            voucher__company=company,
            voucher__status="confirmed",
            tafzili__customer__id=customer_id,
        ).select_related("voucher", "kol", "moin", "tafzili").order_by(
            "voucher__date", "voucher__number"
        )

        return [
            {
                "date": entry.voucher.date,
                "date_jalali": entry.voucher.date_jalali,
                "voucher_number": entry.voucher.number,
                "description": entry.description,
                "debit": entry.debit,
                "credit": entry.credit,
                "kol_name": entry.kol.name,
            }
            for entry in entries
        ]

    @staticmethod
    def get_supplier_ledger(company, supplier_id: int) -> List[Dict]:
        """Get all journal entries related to a specific supplier."""
        entries = JournalEntry.objects.filter(
            voucher__company=company,
            voucher__status="confirmed",
            tafzili__supplier__id=supplier_id,
        ).select_related("voucher", "kol", "moin", "tafzili").order_by(
            "voucher__date", "voucher__number"
        )

        return [
            {
                "date": entry.voucher.date,
                "date_jalali": entry.voucher.date_jalali,
                "voucher_number": entry.voucher.number,
                "description": entry.description,
                "debit": entry.debit,
                "credit": entry.credit,
                "kol_name": entry.kol.name,
            }
            for entry in entries
        ]
