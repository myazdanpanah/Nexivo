"""Custom DRF permissions for db_manager — admin vs updater."""

from django.db import models
from rest_framework.permissions import BasePermission


class IsAdminOrCEO(BasePermission):
    """Allow access only to admin, CEO, or staff users."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.role in ("admin", "ceo") or user.is_staff


class IsUpdaterOrAbove(BasePermission):
    """Allow access to admin/CEO/staff, plus updater-role users with table permissions."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role in ("admin", "ceo") or user.is_staff:
            return True
        return user.role == "updater"


class CanEditTable(BasePermission):
    """Check that the user has edit permission on the specific table.

    Admin/CEO/staff always pass. Updater-role users must have a matching
    DatabasePermission row with can_edit=True for the source/table.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role in ("admin", "ceo") or user.is_staff:
            return True

        from apps.db_manager.models import DatabasePermission

        source = view.kwargs.get("source", "local")
        table = view.kwargs.get("table", "")

        return DatabasePermission.objects.filter(
            user=user,
            database_source=source,
            can_edit=True,
        ).filter(
            models.Q(table_name="*") | models.Q(table_name=table)
        ).exists()
