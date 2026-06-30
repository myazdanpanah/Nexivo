"""Celery tasks for Google Sheets sync."""

from celery import shared_task
from django.utils import timezone


@shared_task
def run_sheets_sync(sync_id):
    """Execute a Google Sheets sync by its config ID."""
    from apps.db_manager.models import GoogleSheetsSync
    from apps.db_manager.services.sheets_sync import sync_from_sheets

    try:
        sync = GoogleSheetsSync.objects.get(pk=sync_id, is_active=True)
    except GoogleSheetsSync.DoesNotExist:
        return {"error": f"Sync config {sync_id} not found or inactive"}

    result = sync_from_sheets(sync)

    sync.last_sync_at = timezone.now()
    sync.last_sync_status = result["status"]
    sync.last_error = result.get("error", "")
    sync.save(update_fields=["last_sync_at", "last_sync_status", "last_error"])

    return result


@shared_task
def check_active_syncs():
    """Periodic task: run all active syncs whose schedule is due."""
    from apps.db_manager.models import GoogleSheetsSync

    active_syncs = GoogleSheetsSync.objects.filter(is_active=True)
    for sync in active_syncs:
        # Run each sync asynchronously
        run_sheets_sync.delay(sync.id)
