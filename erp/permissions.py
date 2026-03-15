# erp/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsHRManager(BasePermission):
    """
    Grants full access only to users in the 'HR Managers' group.
    All other authenticated users get read-only access.
    """

    message = "You must be an HR Manager to perform this action."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        return (
            request.user.is_authenticated
            and request.user.groups.filter(name="HR Managers").exists()
        )


class IsManagerOrReadOnly(BasePermission):
    """
    Staff/managers can write; others can only read.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        return request.user.is_authenticated and request.user.is_staff


class IsOwnerOrManager(BasePermission):
    """
    Object-level permission: allows owners to edit their own objects
    and managers to edit any object.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if hasattr(obj, "employee"):
            return obj.employee.user == request.user

        if hasattr(obj, "user"):
            return obj.user == request.user

        return False
