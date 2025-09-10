from rest_framework.permissions import BasePermission

class DenyIfNoRole(BasePermission):
    """
    Rechaza cualquier interacción a la API si el usuario no posee grupo o no tiene permisos
    a nivel de usuario.
    No aplicable para superuser.
    """
    message = "User has no roles/permissions assigned."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser:
            return True
        has_group = user.groups.exists()
        has_user_perms = user.user_permissions.exists()

        return has_group or has_user_perms
