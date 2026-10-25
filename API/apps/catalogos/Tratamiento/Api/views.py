from rest_framework import viewsets
from apps.catalogos.patient_scope import PatientScopedViewSetMixin
from ..models import Tratamiento
from .serializers import TratamientoSerializer

class TratamientoViewSet(PatientScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Tratamiento.objects.all()
    serializer_class = TratamientoSerializer
    patient_lookup = (
        "id_atencion_cronico__id_paciente_patologia__id_paciente__usuario"
    )
