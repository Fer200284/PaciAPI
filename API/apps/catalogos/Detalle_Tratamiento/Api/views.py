from rest_framework import viewsets
from apps.catalogos.patient_scope import PatientScopedViewSetMixin
from ..models import DetalleTratamiento
from .serializers import DetalleTratamientoSerializer

class DetalleTratamientoViewSet(
    PatientScopedViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = DetalleTratamiento.objects.all()
    serializer_class = DetalleTratamientoSerializer
    patient_lookup = (
        "id_tratamiento__id_atencion_cronico__"
        "id_paciente_patologia__id_paciente__usuario"
    )
