from rest_framework import permissions


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
