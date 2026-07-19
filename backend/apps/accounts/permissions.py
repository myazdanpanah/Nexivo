from rest_framework import permissions
from .models import ALL_MODULE_IDS


class IsOwnerOrAdmin(permissions.BasePermission):
    """Allow access to object owner or admin users."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.role == "admin":
            return True
        return obj.user == request.user


class IsCEO(permissions.BasePermission):
    """Allow access only to CEO users."""

    def has_permission(self, request, view):
        return request.user and request.user.is_ceo


class IsFinanceOrAbove(permissions.BasePermission):
    """Allow access to Finance users and above (CEO, Admin)."""

    def has_permission(self, request, view):
        return request.user.role in ("finance", "ceo", "admin") or request.user.is_staff


class IsSalesOrAbove(permissions.BasePermission):
    """Allow access to Sales users and above."""

    def has_permission(self, request, view):
        return request.user.role in ("sales", "finance", "ceo", "admin") or request.user.is_staff


class RequireModule(permissions.BasePermission):
    """
    DRF permission that checks whether the user's company has a specific
    module enabled.  Use it as a class attribute on any view:

        permission_classes = [RequireModule.for_module("bi_dashboard")]

    Staff users always pass.  Users without a company are denied.
    """

    # Set by the classmethod below
    _required_module: str = ""

    def has_permission(self, request, view):
        # When called from _check_dashboard_module, view is None —
        # fall back to the class-level _required_module in that case.
        required = self._required_module
        if view is not None:
            required = getattr(view, "required_module", None) or required
        if not required:
            return True  # no module gate configured → allow

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        if not user.company:
            return False
        return required in (user.company.enabled_modules or [])

    @classmethod
    def for_module(cls, module_id: str):
        """Return a new permission class that gates on *module_id*."""
        assert module_id in ALL_MODULE_IDS, f"Unknown module: {module_id}"

        class _Perm(cls):
            _required_module = module_id

        _Perm.__name__ = f"RequireModule_{module_id}"
        _Perm.__qualname__ = f"RequireModule.for_module.{module_id}"
        return _Perm
