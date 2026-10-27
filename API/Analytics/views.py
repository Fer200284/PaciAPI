import logging

from django.core.exceptions import ImproperlyConfigured
from pymongo.errors import PyMongoError
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.catalogos.patient_scope import is_patient_user
from .serializers import EncuestaSerializer
from .services import guardar_encuesta


logger = logging.getLogger(__name__)


class EncuestasView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EncuestaSerializer

    def post(self, request):
        if not is_patient_user(request.user):
            raise PermissionDenied(
                "Solo una cuenta Paciente puede enviar una encuesta."
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            encuesta_id = guardar_encuesta(serializer.validated_data)
        except ImproperlyConfigured as error:
            logger.error("MongoDB no está configurado: %s", error)
            return Response(
                {"detail": "El almacenamiento de encuestas no está configurado."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except PyMongoError:
            logger.exception("No se pudo guardar la encuesta en MongoDB.")
            return Response(
                {"detail": "No se pudo guardar la encuesta."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {"id": encuesta_id},
            status=status.HTTP_201_CREATED,
        )
