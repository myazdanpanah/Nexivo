from django.contrib import admin
from .models import Dataset, DataFilter


class DataFilterInline(admin.TabularInline):
    model = DataFilter
    extra = 0


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "row_count", "column_count", "owner", "created_at")
    list_filter = ("status", "allowed_roles")
    search_fields = ("name", "description")
    inlines = [DataFilterInline]
