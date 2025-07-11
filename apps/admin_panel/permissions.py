# admin_panel/permissions.py
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users"""

    def has_permission(self, request, view):
        return request.user and request.user.is_staff
