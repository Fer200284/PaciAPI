from rest_framework import viewsets
from apps.catalogos.patient_scope import PatientScopedViewSetMixin
from ..models import AtencionCronico
from .serializers import AtencionCronicoSerializer

class AtencionCronicoViewSet(PatientScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = AtencionCronico.objects.all()
    serializer_class = AtencionCronicoSerializer
    patient_lookup = "id_paciente_patologia__id_paciente__usuario"
