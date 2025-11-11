from rest_framework import permissions

class IsAccountUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return hasattr(request, 'account') and request.user.is_authenticated

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'admin'

class IsManagerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['admin', 'manager']

class CanEditAssignedOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role in ['admin', 'manager']:
            return True
        return obj.assigned_to == request.user
