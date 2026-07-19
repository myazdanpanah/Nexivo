"""
Finance Module Views — Iranian Accounting System (Sepidar-style)

All endpoints gated by the 'finance' module. Notifications endpoints are ungated.
"""

import logging
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.permissions import RequireModule

from .models import (
    AccountGroup, KolAccount, MoinAccount, TafziliAccount,
    BankAccount, Customer, Supplier, FiscalYear,
    JournalVoucher, JournalEntry,
    Invoice, InvoiceItem, Receipt, Payment, Cheque,
)
from .serializers import (
    AccountGroupSerializer, KolAccountSerializer, MoinAccountSerializer,
    TafziliAccountSerializer, BankAccountSerializer,
    CustomerSerializer, SupplierSerializer, FiscalYearSerializer,
    JournalVoucherSerializer, JournalVoucherCreateSerializer, JournalEntrySerializer,
    InvoiceSerializer, InvoiceCreateSerializer, InvoiceItemSerializer,
    ReceiptSerializer, PaymentSerializer, ChequeSerializer,
)
from .services import (
    ValidationError, FiscalYearService, JournalService,
    InvoiceService, ReceiptService, PaymentService, ChequeService,
)
from .selectors import (
    AccountSelector, CustomerSelector, SupplierSelector,
    FinanceDashboardSelector, JournalSelector, InvoiceSelector,
)

logger = logging.getLogger(__name__)

# ─── Module gate ──────────────────────────────────────────────────
_FinancePerm = RequireModule.for_module("finance")()


def _check_finance_module(request):
    """Return None if OK, or a 403 Response if the module is not enabled."""
    if not _FinancePerm.has_permission(request, None):
        return Response(
            {"error": "Module 'finance' is not enabled for your company"},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


# ─── Fiscal Year ─────────────────────────────────────────────────

@api_view(["GET", "POST"])
def fiscal_year_list(request):
    """List or create fiscal years."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    if request.method == "GET":
        years = FiscalYear.objects.filter(company=request.user.company)
        return Response(FiscalYearSerializer(years, many=True).data)
    elif request.method == "POST":
        data = request.data.copy()
        serializer = FiscalYearSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(company=request.user.company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def fiscal_year_detail(request, pk):
    """Retrieve, update, or delete a fiscal year."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    try:
        fy = FiscalYear.objects.get(pk=pk, company=request.user.company)
    except FiscalYear.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response(FiscalYearSerializer(fy).data)
    elif request.method == "PUT":
        serializer = FiscalYearSerializer(fy, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    elif request.method == "DELETE":
        fy.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Chart of Accounts ───────────────────────────────────────────

@api_view(["GET", "POST"])
def account_group_list(request):
    """List or create account groups."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    if request.method == "GET":
        groups = AccountGroup.objects.filter(company=request.user.company)
        return Response(AccountGroupSerializer(groups, many=True).data)
    elif request.method == "POST":
        data = request.data.copy()
        serializer = AccountGroupSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(company=request.user.company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def kol_account_list(request):
    """List Kol (General Ledger) accounts."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    qs = KolAccount.objects.filter(company=request.user.company).select_related("group")
    group_id = request.query_params.get("group")
    if group_id:
        qs = qs.filter(group_id=group_id)
    return Response(KolAccountSerializer(qs, many=True).data)


@api_view(["GET"])
def moin_account_list(request):
    """List Moin (Subsidiary) accounts."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    qs = MoinAccount.objects.filter(company=request.user.company).select_related("kol")
    kol_id = request.query_params.get("kol")
    if kol_id:
        qs = qs.filter(kol_id=kol_id)
    return Response(MoinAccountSerializer(qs, many=True).data)


@api_view(["GET"])
def tafzili_account_list(request):
    """List Tafzili (Detail) accounts."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    qs = TafziliAccount.objects.filter(company=request.user.company)
    entity_type = request.query_params.get("entity_type")
    if entity_type:
        qs = qs.filter(entity_type=entity_type)
    return Response(TafziliAccountSerializer(qs, many=True).data)


# ─── Chart of Accounts Tree (flat) ──────────────────────────────

@api_view(["GET"])
def chart_of_accounts_tree(request):
    """Return a flat tree of all accounts: Group → Kol → Moin → Tafzili."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    company = request.user.company
    groups = (
        AccountGroup.objects.filter(company=company)
        .order_by("code")
    )
    # Prefetch Kol → Moin → Tafzili in bulk to avoid N+1
    kols_by_group = {}
    for kol in KolAccount.objects.filter(company=company).select_related("group").order_by("code"):
        kols_by_group.setdefault(kol.group_id, []).append(kol)
    moins_by_kol = {}
    for moin in MoinAccount.objects.filter(company=company).select_related("kol").order_by("code"):
        moins_by_kol.setdefault(moin.kol_id, []).append(moin)
    # Tafzili: fetch all linked to any moin in this company
    tafzili_by_moin = {}
    for t in TafziliAccount.objects.filter(
        company=company, linked_moin_accounts__isnull=False
    ).prefetch_related("linked_moin_accounts").order_by("code"):
        for m in t.linked_moin_accounts.all():
            tafzili_by_moin.setdefault(m.id, []).append(t)
    tree = []
    for grp in groups:
        kol_list = []
        for kol in kols_by_group.get(grp.id, []):
            moin_list = []
            for moin in moins_by_kol.get(kol.id, []):
                moin_list.append({
                    "id": moin.id,
                    "code": moin.code,
                    "name": moin.name,
                    "tafzilis": TafziliAccountSerializer(
                        tafzili_by_moin.get(moin.id, []), many=True
                    ).data,
                })
            kol_list.append({
                "id": kol.id,
                "code": kol.code,
                "name": kol.name,
                "account_type": kol.account_type,
                "normal_balance": kol.normal_balance,
                "moins": moin_list,
            })
        tree.append({
            "id": grp.id,
            "code": grp.code,
            "name": grp.name,
            "kols": kol_list,
        })
    return Response(tree)


# ─── Bank Accounts ───────────────────────────────────────────────

@api_view(["GET", "POST"])
def bank_account_list(request):
    """List or create bank accounts."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    if request.method == "GET":
        accounts = BankAccount.objects.filter(company=request.user.company)
        return Response(BankAccountSerializer(accounts, many=True).data)
    elif request.method == "POST":
        data = request.data.copy()
        serializer = BankAccountSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(company=request.user.company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def bank_account_detail(request, pk):
    """Retrieve, update, or delete a bank account."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    try:
        ba = BankAccount.objects.get(pk=pk, company=request.user.company)
    except BankAccount.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response(BankAccountSerializer(ba).data)
    elif request.method == "PUT":
        serializer = BankAccountSerializer(ba, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    elif request.method == "DELETE":
        ba.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Customers ───────────────────────────────────────────────────

@api_view(["GET", "POST"])
def customer_list(request):
    """List or create customers."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    if request.method == "GET":
        customers = Customer.objects.filter(company=request.user.company)
        q = request.query_params.get("q")
        if q:
            customers = customers.filter(
                Q(name__icontains=q) | Q(national_id__icontains=q)
            )
        return Response(CustomerSerializer(customers, many=True).data)
    elif request.method == "POST":
        data = request.data.copy()
        serializer = CustomerSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(company=request.user.company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def customer_detail(request, pk):
    """Retrieve, update, or delete a customer."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    try:
        c = Customer.objects.get(pk=pk, company=request.user.company)
    except Customer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response(CustomerSerializer(c).data)
    elif request.method == "PUT":
        serializer = CustomerSerializer(c, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    elif request.method == "DELETE":
        c.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Suppliers ───────────────────────────────────────────────────

@api_view(["GET", "POST"])
def supplier_list(request):
    """List or create suppliers."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    if request.method == "GET":
        suppliers = Supplier.objects.filter(company=request.user.company)
        q = request.query_params.get("q")
        if q:
            suppliers = suppliers.filter(
                Q(name__icontains=q) | Q(national_id__icontains=q)
            )
        return Response(SupplierSerializer(suppliers, many=True).data)
    elif request.method == "POST":
        data = request.data.copy()
        serializer = SupplierSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(company=request.user.company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def supplier_detail(request, pk):
    """Retrieve, update, or delete a supplier."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    try:
        s = Supplier.objects.get(pk=pk, company=request.user.company)
    except Supplier.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response(SupplierSerializer(s).data)
    elif request.method == "PUT":
        serializer = SupplierSerializer(s, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    elif request.method == "DELETE":
        s.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Journal Vouchers (Sanad) ────────────────────────────────────

@api_view(["GET", "POST"])
def journal_voucher_list(request):
    """List or create journal vouchers."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    company = request.user.company
    if request.method == "GET":
        qs = JournalVoucher.objects.filter(company=company).select_related(
            "fiscal_year", "created_by"
        )
        fiscal_year_id = request.query_params.get("fiscal_year")
        if fiscal_year_id:
            qs = qs.filter(fiscal_year_id=fiscal_year_id)
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response(JournalVoucherSerializer(qs, many=True).data)

    elif request.method == "POST":
        # Auto-resolve fiscal_year from current open FY if not provided
        fy_id = request.data.get("fiscal_year")
        if not fy_id:
            fy = FiscalYear.objects.filter(company=company, is_closed=False).first()
            if not fy:
                return Response(
                    {"error": "No open fiscal year found. Create one first."},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            fy_id = fy.id
        data = request.data.copy()
        data["company"] = company.id
        data["fiscal_year"] = fy_id
        data["created_by"] = request.user.id
        # Auto-assign next voucher number per fiscal year
        last = JournalVoucher.objects.filter(
            company=company, fiscal_year_id=fy_id
        ).order_by("-number").first()
        data["number"] = (last.number + 1) if last else 1
        serializer = JournalVoucherCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        voucher = serializer.save(
            company=company, fiscal_year_id=fy_id, created_by=request.user
        )
        return Response(
            JournalVoucherSerializer(voucher).data,
            status=status.HTTP_201_CREATED,
        )


@api_view(["GET", "PUT", "DELETE"])
def journal_voucher_detail(request, pk):
    """Retrieve, update, or delete a journal voucher."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    try:
        voucher = JournalVoucher.objects.get(pk=pk, company=request.user.company)
    except JournalVoucher.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response(JournalVoucherSerializer(voucher).data)
    elif request.method == "PUT":
        serializer = JournalVoucherCreateSerializer(voucher, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        voucher = serializer.save()
        return Response(JournalVoucherSerializer(voucher).data)
    elif request.method == "DELETE":
        voucher.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def journal_voucher_confirm(request, pk):
    """Confirm a journal voucher — delegates to JournalService."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    try:
        voucher = JournalVoucher.objects.get(pk=pk, company=request.user.company)
    except JournalVoucher.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    try:
        voucher = JournalService.confirm_voucher(voucher, request.user)
        return Response(JournalVoucherSerializer(voucher).data)
    except ValidationError as e:
        return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


# ─── Invoices (Factor) ───────────────────────────────────────────

@api_view(["GET", "POST"])
def invoice_list(request):
    """List or create invoices (factors)."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    company = request.user.company
    fy = FiscalYear.objects.filter(company=company, is_closed=False).first()
    if request.method == "GET":
        qs = Invoice.objects.filter(company=company).select_related(
            "fiscal_year", "customer", "supplier", "created_by"
        )
        invoice_type = request.query_params.get("type")
        if invoice_type:
            qs = qs.filter(type=invoice_type)
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response(InvoiceSerializer(qs, many=True).data)

    elif request.method == "POST":
        if not fy:
            return Response(
                {"error": "No open fiscal year found. Create one first."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        data = request.data.copy()
        data["company"] = company.id
        data["fiscal_year"] = fy.id
        data["created_by"] = request.user.id
        # Auto-assign next number
        invoice_type = data.get("type", "sales")
        last = (
            Invoice.objects.filter(company=company, fiscal_year=fy, type=invoice_type)
            .order_by("-number")
            .first()
        )
        data["number"] = (last.number + 1) if last else 1
        serializer = InvoiceCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        invoice = serializer.save(
            company=company, fiscal_year=fy, created_by=request.user
        )
        return Response(
            InvoiceSerializer(invoice).data,
            status=status.HTTP_201_CREATED,
        )


@api_view(["GET", "PUT", "DELETE"])
def invoice_detail(request, pk):
    """Retrieve, update, or delete an invoice."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    try:
        invoice = Invoice.objects.get(pk=pk, company=request.user.company)
    except Invoice.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response(InvoiceSerializer(invoice).data)
    elif request.method == "PUT":
        serializer = InvoiceCreateSerializer(invoice, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        invoice = serializer.save()
        return Response(InvoiceSerializer(invoice).data)
    elif request.method == "DELETE":
        invoice.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def invoice_confirm(request, pk):
    """Confirm an invoice — delegates to InvoiceService."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    try:
        invoice = Invoice.objects.get(pk=pk, company=request.user.company)
    except Invoice.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    try:
        invoice = InvoiceService.confirm_invoice(invoice, request.user)
        return Response(InvoiceSerializer(invoice).data)
    except ValidationError as e:
        return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


# ─── Receipts (Daryaft / واریزی) ────────────────────────────────

@api_view(["GET", "POST"])
def receipt_list(request):
    """List or create receipts."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    company = request.user.company
    fy = FiscalYear.objects.filter(company=company, is_closed=False).first()
    if request.method == "GET":
        qs = Receipt.objects.filter(company=company).select_related(
            "fiscal_year", "customer", "bank_account", "created_by"
        )
        return Response(ReceiptSerializer(qs, many=True).data)
    elif request.method == "POST":
        if not fy:
            return Response(
                {"error": "No open fiscal year found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Company-scope FKs: validate customer and bank_account belong to this company
        customer_id = request.data.get("customer")
        bank_account_id = request.data.get("bank_account")
        if customer_id and not Customer.objects.filter(pk=customer_id, company=company).exists():
            return Response({"error": "Customer not found in your company"}, status=status.HTTP_400_BAD_REQUEST)
        if bank_account_id and not BankAccount.objects.filter(pk=bank_account_id, company=company).exists():
            return Response({"error": "Bank account not found in your company"}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data.copy()
        data["company"] = company.id
        data["fiscal_year"] = fy.id
        data["created_by"] = request.user.id
        last = Receipt.objects.filter(company=company, fiscal_year=fy).order_by("-number").first()
        data["number"] = (last.number + 1) if last else 1
        serializer = ReceiptSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        receipt = serializer.save(
            company=company, fiscal_year=fy, created_by=request.user
        )
        return Response(ReceiptSerializer(receipt).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def receipt_detail(request, pk):
    """Retrieve, update, or delete a receipt."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    try:
        receipt = Receipt.objects.get(pk=pk, company=request.user.company)
    except Receipt.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response(ReceiptSerializer(receipt).data)
    elif request.method == "PUT":
        serializer = ReceiptSerializer(receipt, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ReceiptSerializer(receipt).data)
    elif request.method == "DELETE":
        receipt.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Payments (Pardakht / پرداختی) ──────────────────────────────

@api_view(["GET", "POST"])
def payment_list(request):
    """List or create payments."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    company = request.user.company
    fy = FiscalYear.objects.filter(company=company, is_closed=False).first()
    if request.method == "GET":
        qs = Payment.objects.filter(company=company).select_related(
            "fiscal_year", "supplier", "bank_account", "created_by"
        )
        return Response(PaymentSerializer(qs, many=True).data)
    elif request.method == "POST":
        if not fy:
            return Response(
                {"error": "No open fiscal year found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Company-scope FKs: validate supplier and bank_account belong to this company
        supplier_id = request.data.get("supplier")
        bank_account_id = request.data.get("bank_account")
        if supplier_id and not Supplier.objects.filter(pk=supplier_id, company=company).exists():
            return Response({"error": "Supplier not found in your company"}, status=status.HTTP_400_BAD_REQUEST)
        if bank_account_id and not BankAccount.objects.filter(pk=bank_account_id, company=company).exists():
            return Response({"error": "Bank account not found in your company"}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data.copy()
        data["company"] = company.id
        data["fiscal_year"] = fy.id
        data["created_by"] = request.user.id
        last = Payment.objects.filter(company=company, fiscal_year=fy).order_by("-number").first()
        data["number"] = (last.number + 1) if last else 1
        serializer = PaymentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save(
            company=company, fiscal_year=fy, created_by=request.user
        )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def payment_detail(request, pk):
    """Retrieve, update, or delete a payment."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    try:
        payment = Payment.objects.get(pk=pk, company=request.user.company)
    except Payment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response(PaymentSerializer(payment).data)
    elif request.method == "PUT":
        serializer = PaymentSerializer(payment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(PaymentSerializer(payment).data)
    elif request.method == "DELETE":
        payment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Cheques ─────────────────────────────────────────────────────

@api_view(["GET", "POST"])
def cheque_list(request):
    """List or create cheques."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    if request.method == "GET":
        qs = Cheque.objects.filter(company=request.user.company)
        cheque_type = request.query_params.get("cheque_type")
        if cheque_type:
            qs = qs.filter(cheque_type=cheque_type)
        cheque_status = request.query_params.get("status")
        if cheque_status:
            qs = qs.filter(status=cheque_status)
        return Response(ChequeSerializer(qs, many=True).data)
    elif request.method == "POST":
        # Company-scope FKs: validate customer/supplier belong to this company
        company = request.user.company
        customer_id = request.data.get("customer")
        supplier_id = request.data.get("supplier")
        if customer_id and not Customer.objects.filter(pk=customer_id, company=company).exists():
            return Response({"error": "Customer not found in your company"}, status=status.HTTP_400_BAD_REQUEST)
        if supplier_id and not Supplier.objects.filter(pk=supplier_id, company=company).exists():
            return Response({"error": "Supplier not found in your company"}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data.copy()
        serializer = ChequeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(company=company)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
def cheque_detail(request, pk):
    """Retrieve, update, or delete a cheque."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    try:
        cheque = Cheque.objects.get(pk=pk, company=request.user.company)
    except Cheque.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response(ChequeSerializer(cheque).data)
    elif request.method == "PUT":
        serializer = ChequeSerializer(cheque, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    elif request.method == "DELETE":
        cheque.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Reports / Summary ──────────────────────────────────────────

@api_view(["GET"])
def finance_summary(request):
    """Return a financial summary — delegates to FinanceDashboardSelector."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    summary = FinanceDashboardSelector.get_summary(request.user.company)
    fy = summary.pop("fiscal_year", None)
    summary["fiscal_year"] = FiscalYearSerializer(fy).data if fy else None
    return Response(summary)


@api_view(["GET"])
def customer_balances(request):
    """List all customer balances."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    customers = Customer.objects.filter(company=request.user.company, is_active=True).order_by("name")
    data = [
        {"id": c.id, "name": c.name, "national_id": c.national_id, "balance": c.balance}
        for c in customers
    ]
    return Response(data)


@api_view(["GET"])
def supplier_balances(request):
    """List all supplier balances."""
    gate = _check_finance_module(request)
    if gate:
        return gate
    suppliers = Supplier.objects.filter(company=request.user.company, is_active=True).order_by("name")
    data = [
        {"id": s.id, "name": s.name, "national_id": s.national_id, "balance": s.balance}
        for s in suppliers
    ]
    return Response(data)
