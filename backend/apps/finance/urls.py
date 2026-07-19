from django.urls import path
from . import views

urlpatterns = [
    # Fiscal Year
    path("fiscal-years/", views.fiscal_year_list, name="fy-list"),
    path("fiscal-years/<int:pk>/", views.fiscal_year_detail, name="fy-detail"),
    # Chart of Accounts
    path("accounts/groups/", views.account_group_list, name="ag-list"),
    path("accounts/kol/", views.kol_account_list, name="kol-list"),
    path("accounts/moin/", views.moin_account_list, name="moin-list"),
    path("accounts/tafzili/", views.tafzili_account_list, name="tafzili-list"),
    path("accounts/tree/", views.chart_of_accounts_tree, name="coa-tree"),
    # Bank Accounts
    path("bank-accounts/", views.bank_account_list, name="bank-list"),
    path("bank-accounts/<int:pk>/", views.bank_account_detail, name="bank-detail"),
    # Customers
    path("customers/", views.customer_list, name="customer-list"),
    path("customers/<int:pk>/", views.customer_detail, name="customer-detail"),
    path("customers/balances/", views.customer_balances, name="customer-balances"),
    # Suppliers
    path("suppliers/", views.supplier_list, name="supplier-list"),
    path("suppliers/<int:pk>/", views.supplier_detail, name="supplier-detail"),
    path("suppliers/balances/", views.supplier_balances, name="supplier-balances"),
    # Journal Vouchers
    path("vouchers/", views.journal_voucher_list, name="voucher-list"),
    path("vouchers/<int:pk>/", views.journal_voucher_detail, name="voucher-detail"),
    path("vouchers/<int:pk>/confirm/", views.journal_voucher_confirm, name="voucher-confirm"),
    # Invoices
    path("invoices/", views.invoice_list, name="invoice-list"),
    path("invoices/<int:pk>/", views.invoice_detail, name="invoice-detail"),
    path("invoices/<int:pk>/confirm/", views.invoice_confirm, name="invoice-confirm"),
    # Receipts
    path("receipts/", views.receipt_list, name="receipt-list"),
    path("receipts/<int:pk>/", views.receipt_detail, name="receipt-detail"),
    # Payments
    path("payments/", views.payment_list, name="payment-list"),
    path("payments/<int:pk>/", views.payment_detail, name="payment-detail"),
    # Cheques
    path("cheques/", views.cheque_list, name="cheque-list"),
    path("cheques/<int:pk>/", views.cheque_detail, name="cheque-detail"),
    # Reports
    path("summary/", views.finance_summary, name="finance-summary"),
    path("trial-balance/", views.trial_balance, name="trial-balance"),
]
