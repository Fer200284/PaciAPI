import logging

from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from pymongo.errors import PyMongoError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import (
    APIException,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response

from Analytics.services import (
    eliminar_atencion,
    guardar_atencion_desde_modelo,
)
from apps.catalogos.patient_scope import (
    PatientScopedViewSetMixin,
    is_patient_user,
)
from apps.Seguridad.Usuarios.models import User
from ..models import AtencionCronico
from .serializers import AtencionCronicoSerializer


logger = logging.getLogger(__name__)


class AnalyticsStorageUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = (
        "No se pudo sincronizar la atención con MongoDB. "
        "Los cambios operacionales no se guardaron."
    )
    default_code = "analytics_storage_unavailable"


class AtencionHasRelatedRecords(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = (
        "No se puede eliminar la atención porque tiene tratamientos o "
        "solicitudes de examen vinculados."
    )
    default_code = "atencion_has_related_records"


class AtencionCronicoViewSet(PatientScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = AtencionCronico.objects.all()
    serializer_class = AtencionCronicoSerializer
    patient_lookup = "id_paciente_patologia__id_paciente__usuario"

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                super().perform_create(serializer)
                guardar_atencion_desde_modelo(serializer.instance)
        except ImproperlyConfigured as error:
            logger.error("MongoDB no está configurado: %s", error)
            raise AnalyticsStorageUnavailable() from error
        except PyMongoError as error:
            logger.exception("No se pudo guardar la atención analítica en MongoDB.")
            raise AnalyticsStorageUnavailable() from error

    def perform_update(self, serializer):
        try:
            with transaction.atomic():
                super().perform_update(serializer)
                guardar_atencion_desde_modelo(serializer.instance)
        except ImproperlyConfigured as error:
            logger.error("MongoDB no está configurado: %s", error)
            raise AnalyticsStorageUnavailable() from error
        except PyMongoError as error:
            logger.exception(
                "No se pudo actualizar la atención analítica en MongoDB."
            )
            raise AnalyticsStorageUnavailable() from error

    def perform_destroy(self, instance):
        id_atencion = instance.pk
        try:
            with transaction.atomic():
                super().perform_destroy(instance)
                eliminar_atencion(id_atencion)
        except ProtectedError as error:
            raise AtencionHasRelatedRecords() from error
        except ImproperlyConfigured as error:
            logger.error("MongoDB no está configurado: %s", error)
            raise AnalyticsStorageUnavailable() from error
        except PyMongoError as error:
            logger.exception(
                "No se pudo eliminar la atención analítica en MongoDB."
            )
            raise AnalyticsStorageUnavailable() from error

    def _registrar_momento(self, request, pk, campo, requiere=None):
        usuario = request.user
        es_personal = getattr(usuario, "rol", None) in {
            User.Roles.ADMINISTRADOR,
            User.Roles.GERENCIA,
        }
        if campo == "fecha_hora_llegada":
            if not (is_patient_user(usuario) or es_personal):
                raise PermissionDenied(
                    "Solo el paciente o el personal autorizado puede marcar la llegada."
                )
        elif not es_personal:
            raise PermissionDenied(
                "Solo el personal autorizado puede registrar el inicio o fin "
                "de la consulta."
            )

        try:
            with transaction.atomic():
                atencion = self.get_object()
                if getattr(atencion, campo) is not None:
                    raise ValidationError({
                        campo: "Este momento ya fue registrado."
                    })
                if requiere and getattr(atencion, requiere) is None:
                    raise ValidationError({
                        campo: "Registra primero el momento anterior."
                    })

                setattr(atencion, campo, timezone.now())
                update_fields = [campo]
                if campo == "fecha_hora_llegada":
                    atencion.asistio = True
                    update_fields.append("asistio")
                atencion.save(update_fields=update_fields)
                guardar_atencion_desde_modelo(atencion)
        except ImproperlyConfigured as error:
            logger.error("MongoDB no está configurado: %s", error)
            raise AnalyticsStorageUnavailable() from error
        except PyMongoError as error:
            logger.exception(
                "No se pudo sincronizar la marca de tiempo de la atención."
            )
            raise AnalyticsStorageUnavailable() from error

        return Response(self.get_serializer(atencion).data)

    @action(detail=True, methods=["post"], url_path="marcar-llegada")
    def marcar_llegada(self, request, pk=None):
        return self._registrar_momento(
            request,
            pk,
            "fecha_hora_llegada",
        )

    @action(detail=True, methods=["post"], url_path="iniciar-consulta")
    def iniciar_consulta(self, request, pk=None):
        return self._registrar_momento(
            request,
            pk,
            "fecha_hora_inicio_consulta",
            requiere="fecha_hora_llegada",
        )

    @action(detail=True, methods=["post"], url_path="finalizar-consulta")
    def finalizar_consulta(self, request, pk=None):
        return self._registrar_momento(
            request,
            pk,
            "fecha_hora_fin_consulta",
            requiere="fecha_hora_inicio_consulta",
        )
