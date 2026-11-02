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
