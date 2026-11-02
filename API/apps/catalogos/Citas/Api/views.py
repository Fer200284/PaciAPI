from django.utils import timezone
from rest_framework import viewsets

from apps.catalogos.patient_scope import PatientScopedViewSetMixin
from ..models import Citas
from .serializers import CitasSerializer


class CitasViewSet(
    PatientScopedViewSetMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = Citas.objects.select_related("id_paciente", "id_medico")
    serializer_class = CitasSerializer
    patient_lookup = "id_paciente__usuario"

    def get_queryset(self):
        return super().get_queryset().filter(
            estado=Citas.Estado.PROGRAMADA,
            fecha_hora_cita__gt=timezone.now(),
        )
