from django.db.models import Prefetch, Q
from django.utils import timezone
from rest_framework import viewsets

from apps.catalogos.Atención_cronico.models import AtencionCronico
from apps.catalogos.patient_scope import PatientScopedViewSetMixin
from ..models import Citas
from .serializers import CitasSerializer


class CitasViewSet(
    PatientScopedViewSetMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = Citas.objects.select_related(
        "id_paciente",
        "id_medico",
    ).prefetch_related(
        Prefetch(
            "atenciones",
            queryset=AtencionCronico.objects.order_by("pk"),
            to_attr="_atenciones_cita",
        )
    )
    serializer_class = CitasSerializer
    patient_lookup = "id_paciente__usuario"

    def get_queryset(self):
        ahora = timezone.now()
        return super().get_queryset().filter(
            estado=Citas.Estado.PROGRAMADA,
        ).filter(
            Q(fecha_hora_cita__gt=ahora)
            | Q(
                fecha_hora_cita__date=timezone.localdate(),
                atenciones__fecha_hora_fin_consulta__isnull=True,
            )
        ).distinct()
