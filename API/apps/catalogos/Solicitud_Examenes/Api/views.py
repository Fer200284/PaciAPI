from rest_framework import viewsets
from apps.catalogos.patient_scope import PatientScopedViewSetMixin
from ..models import SolicitudDeExamenes
from .serializers import SolicitudDeExamenesSerializer

class SolicitudDeExamenesViewSet(
    PatientScopedViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = SolicitudDeExamenes.objects.all()
    serializer_class = SolicitudDeExamenesSerializer
    patient_lookup = (
        "id_atencion_cronico__id_paciente_patologia__id_paciente__usuario"
    )
