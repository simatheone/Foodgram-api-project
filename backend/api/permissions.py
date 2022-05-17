from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.models import USER_ROLE_ADMIN


class IsAdminOrReadOnly(BasePermission):
    """
    Permission for admin, superuser.
    Admin and superuser has permissions for reading/writing.
    Users have permissions for reading.
    """
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or (
            request.user.is_authenticated
            and (request.user.is_superuser
                 or request.user.role == USER_ROLE_ADMIN)
            )


class IsOwnerAdminOrReadOnly(BasePermission):
    """
    Permission for admin, superuser, owner.
    Admin and superuser have permissions for writing.
    """
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
            or request.user.role == USER_ROLE_ADMIN
            or request.user.is_superuser
        )
