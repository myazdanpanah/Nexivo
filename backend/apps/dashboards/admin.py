from django.contrib import admin
from .models import Dashboard, Widget


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
