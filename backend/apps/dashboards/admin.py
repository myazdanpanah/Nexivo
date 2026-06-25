from django.contrib import admin
from .models import Dashboard, Widget, DashboardAssignment, PermissionAuditLog


class WidgetInline(admin.TabularInline):
    model = Widget
    extra = 0
    fields = ("title", "chart_type", "dataset", "grid_x", "grid_y", "grid_w", "grid_h")


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "is_published", "created_at")
    list_filter = ("is_published", "allowed_roles")
    search_fields = ("name", "description")
    inlines = [WidgetInline]


@admin.register(DashboardAssignment)
class DashboardAssignmentAdmin(admin.ModelAdmin):
    list_display = ("dashboard", "assigned_to", "assigned_by", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("dashboard__name", "assigned_to__username", "notes")
    raw_id_fields = ("dashboard", "assigned_to", "assigned_by")


@admin.register(PermissionAuditLog)
class PermissionAuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "target_type", "target_id", "created_at")
    list_filter = ("action", "target_type")
    search_fields = ("target_name", "user__username")
    readonly_fields = ("action", "user", "target_type", "target_id", "target_name", "old_value", "new_value", "details", "created_at")
