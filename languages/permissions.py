from rest_framework import permissions


class LanguagePermission(permissions.BasePermission):
    """
    Custom permission for Language model:
    - Read access for everyone
    - Write access only for staff users
    """

    def has_permission(self, request, view):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for staff users
        return request.user and request.user.is_authenticated and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for staff users
        return request.user and request.user.is_authenticated and request.user.is_staff
