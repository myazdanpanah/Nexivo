from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .role_filters import RoleFilter  # noqa: F401 — ensures RoleFilter is discovered


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "is_active")
    list_filter = ("role", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Role & Permissions", {"fields": ("role", "department")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Role & Permissions", {"fields": ("role", "department")}),
    )
