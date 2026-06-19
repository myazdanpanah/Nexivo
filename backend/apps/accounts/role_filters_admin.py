from django.contrib import admin
from .role_filters import RoleFilter


@admin.register(RoleFilter)
class RoleFilterAdmin(admin.ModelAdmin):
    list_display = ("role", "filter_name", "filter_column", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("filter_name", "filter_column")
