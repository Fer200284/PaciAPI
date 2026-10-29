import logging

from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from pymongo.errors import PyMongoError
from rest_framework import status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from Analytics.services import guardar_atencion_desde_modelo
from apps.catalogos.patient_scope import PatientScopedViewSetMixin
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
