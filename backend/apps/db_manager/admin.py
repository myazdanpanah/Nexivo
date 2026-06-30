from django.contrib import admin
from .models import ExternalDatabase, DatabasePermission, GoogleSheetsSync


@admin.register(ExternalDatabase)
class ExternalDatabaseAdmin(admin.ModelAdmin):
    list_display = ("name", "host", "port", "database", "is_active", "owner")
    list_filter = ("is_active",)


@admin.register(DatabasePermission)
class DatabasePermissionAdmin(admin.ModelAdmin):
    list_display = ("user", "database_source", "table_name", "can_edit", "can_schema", "can_import")
    list_filter = ("database_source", "can_edit")


@admin.register(GoogleSheetsSync)
class GoogleSheetsSyncAdmin(admin.ModelAdmin):
    list_display = ("name", "spreadsheet_id", "table_name", "sync_mode", "is_active", "last_sync_status")
    list_filter = ("is_active", "sync_mode", "last_sync_status")
