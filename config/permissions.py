from rest_framework import permissions


class ReadOnlyForAllPermission(permissions.BasePermission):
    """
    Custom permission that allows:
    - Read access (GET, HEAD, OPTIONS) for everyone
    - Write access only for authenticated users
    """
    
    def has_permission(self, request, view):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for authenticated users
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for authenticated users
        return request.user and request.user.is_authenticated


class ReadOnlyForAllStaffWritePermission(permissions.BasePermission):
    """
    Custom permission that allows:
    - Read access (GET, HEAD, OPTIONS) for everyone
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


class ReadOnlyForAllSuperadminWritePermission(permissions.BasePermission):
    """
    Custom permission that allows:
    - Read access (GET, HEAD, OPTIONS) for everyone
    - Write access only for superadmin users
    """
    
    def has_permission(self, request, view):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for superadmin users
        return request.user and request.user.is_authenticated and request.user.is_superuser
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for superadmin users
        return request.user and request.user.is_authenticated and request.user.is_superuser