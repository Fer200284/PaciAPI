from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.catalogos.Atención_cronico.models import AtencionCronico
from apps.catalogos.patient_scope import (
    PatientScopedViewSetMixin,
    is_patient_user,
)
from apps.Seguridad.Usuarios.models import User
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
        return super().get_queryset().filter(
            Q(estado=Citas.Estado.ASISTIO)
            | Q(
                estado=Citas.Estado.PROGRAMADA,
                fecha_hora_cita__gte=timezone.now(),
            )
        ).distinct()

    @action(detail=True, methods=["post"], url_path="marcar-llegada")
    def marcar_llegada(self, request, pk=None):
        usuario = request.user
        es_personal = getattr(usuario, "rol", None) in {
            User.Roles.ADMINISTRADOR,
            User.Roles.GERENCIA,
        }
        if not (is_patient_user(usuario) or es_personal):
            raise PermissionDenied(
                "Solo el paciente o el personal autorizado puede marcar "
                "la llegada de la cita."
            )

        with transaction.atomic():
            cita = self.get_object()
            if cita.estado != Citas.Estado.PROGRAMADA:
                raise ValidationError({
                    "estado": (
                        "Solo se puede marcar la llegada de una cita "
                        "programada."
                    )
                })

            actualizadas = Citas.objects.filter(
                pk=cita.pk,
                estado=Citas.Estado.PROGRAMADA,
            ).update(
                estado=Citas.Estado.ASISTIO,
                fecha_atencion_real=timezone.now(),
            )
            if not actualizadas:
                raise ValidationError({
                    "estado": "La cita ya fue actualizada por otro usuario."
                })

            cita.refresh_from_db()

        return Response(
            self.get_serializer(cita).data,
            status=status.HTTP_200_OK,
        )
