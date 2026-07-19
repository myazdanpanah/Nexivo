"""
Finance Module Celery Tasks — Background jobs.

Per DJANGO_BACKEND.md §9: Standard app structure includes tasks.py.
Per DJANGO_BACKEND.md §29: Celery Background Jobs.

Future tasks will handle:
- Large PDF invoice generation (async)
- Excel/CSV report export (async)
- Financial period closing batch jobs
- Tax calculation for large datasets
- Scheduled financial report generation
"""
from celery import shared_task


@shared_task(name="finance.generate_invoice_pdf")
def generate_invoice_pdf(invoice_id: int) -> str:
    """Generate PDF for an invoice asynchronously."""
    # Placeholder — will be implemented with reportlab/weasyprint
    return f"Invoice #{invoice_id} PDF generated (placeholder)."


@shared_task(name="finance.export_financial_report")
def export_financial_report(report_type: str, fiscal_year_id: int, format: str = "xlsx") -> str:
    """Export a financial report to Excel/CSV asynchronously."""
    # Placeholder — will be implemented with openpyxl
    return f"Report '{report_type}' for FY#{fiscal_year_id} exported as {format} (placeholder)."
