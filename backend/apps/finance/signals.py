"""
Finance Module Signals — Domain event hooks.

Per DJANGO_BACKEND.md §9: Standard app structure includes signals.py.
Per DJANGO_BACKEND.md §51: Domain Events — every important business action
produces a Domain Event.

Currently signals are intentionally minimal. Future signals will handle:
- InvoiceCreated → Notification Engine, Workflow Engine
- PaymentReceived → Accounting Posting, Notification
- ChequeStatusChanged → Notification, Audit Trail
"""
