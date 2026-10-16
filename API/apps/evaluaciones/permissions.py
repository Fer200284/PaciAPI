from rest_framework.permissions import BasePermission


class IsGerencia(BasePermission):
    message = "Solo Gerencia puede consultar la información gerencial."

    def has_permission(self, request, view):
        return getattr(request.user, "rol", None) == "Gerencia"
