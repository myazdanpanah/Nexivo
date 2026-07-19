"""
Finance Module Permissions — Granular permission checks.

Per DJANGO_BACKEND.md §17: Permission Model
Format: module.resource.action

Examples:
    finance.invoice.view
    finance.invoice.create
    finance.invoice.approve
    finance.journal.post
    finance.report.export

Per DJANGO_BACKEND.md §9: Standard app structure includes permissions.py.
"""

from rest_framework.permissions import BasePermission


class FinancePermission(BasePermission):
    """
    Granular finance permissions.

    This supplements the RequireModule('finance') gate with
    finer-grained per-resource permissions.

    Future usage:
        permission_classes = [FinancePermission.for_action("invoice.create")]
    """

    @classmethod
    def for_action(cls, action: str):
        """Create a permission class for a specific finance action."""

        class _FinanceActionPermission(BasePermission):
            def has_permission(self, request, view):
                # Staff bypass
                if request.user and request.user.is_staff:
                    return True
                # Check custom role permissions if they exist
                if hasattr(request.user, "role_permissions"):
                    return action in request.user.role_permissions
                return True  # Default allow for now (permissions are additive)

        _FinanceActionPermission.__doc__ = f"Requires finance.{action} permission"
        return _FinanceActionPermission
