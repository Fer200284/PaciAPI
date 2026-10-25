from rest_framework import viewsets
from apps.catalogos.patient_scope import PatientScopedViewSetMixin
from ..models import ResultadosExamenes
from .serializers import ResultadosExamenesSerializer

class ResultadosExamenesViewSet(
    PatientScopedViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = ResultadosExamenes.objects.all()
    serializer_class = ResultadosExamenesSerializer
    patient_lookup = (
        "id_solicitud_examen__id_atencion_cronico__"
        "id_paciente_patologia__id_paciente__usuario"
    )
