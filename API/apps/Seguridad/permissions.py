from rest_framework.permissions import BasePermission


class IsAdministrador(BasePermission):
    """
    Permite el acceso únicamente a usuarios con rol Administrador.
    """

    message = "Solo los usuarios con rol Administrador pueden acceder desde la web."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.rol == "Administrador"
        )
