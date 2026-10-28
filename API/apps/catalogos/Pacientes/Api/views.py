from rest_framework import viewsets
from apps.catalogos.patient_scope import PatientScopedViewSetMixin
from ..models import Pacientes
from .serializers import PacientesSerializer


class PacientesViewSet(PatientScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Pacientes.objects.all()
    serializer_class = PacientesSerializer
    patient_lookup = "usuario"

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self.request.user, "rol", None) == "Gerencia":
            return queryset.filter(usuario__isnull=False)
        return queryset