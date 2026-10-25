from rest_framework import viewsets
from apps.catalogos.patient_scope import PatientScopedViewSetMixin
from ..models import Pacientes
from .serializers import PacientesSerializer

class PacientesViewSet(PatientScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Pacientes.objects.all()
    serializer_class = PacientesSerializer
    patient_lookup = "usuario"