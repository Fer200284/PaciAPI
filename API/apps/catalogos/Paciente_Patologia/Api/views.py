from rest_framework import viewsets
from apps.catalogos.patient_scope import PatientScopedViewSetMixin
from ..models import PacientePatologia
from .serializers import PacientePatologiaSerializer

class PacientePatologiaViewSet(PatientScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = PacientePatologia.objects.all()
    serializer_class = PacientePatologiaSerializer
    patient_lookup = "id_paciente__usuario"
