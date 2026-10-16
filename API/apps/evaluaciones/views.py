import logging

from django.core.exceptions import ImproperlyConfigured
from pymongo.errors import PyMongoError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .mongo import get_evaluaciones_collection, get_reportes_collection
from .permissions import IsGerencia
from .reportes import crear_reporte_gerencial


logger = logging.getLogger(__name__)


class EvaluacionesView(APIView):
    def get_permissions(self):
        permissions = [IsAuthenticated]
        if self.request.method == "GET":
            permissions.append(IsGerencia)
        return [permission() for permission in permissions]

    def get(self, request):
        try:
            evaluaciones = list(
                get_evaluaciones_collection().find({}, {"_id": 0})
            )
        except ImproperlyConfigured as error:
            logger.error("MongoDB no está configurado: %s", error)
            return Response(
                {"detail": "El almacenamiento de evaluaciones no está configurado."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except PyMongoError:
            logger.exception("No se pudieron consultar las evaluaciones en MongoDB.")
            return Response(
                {"detail": "No se pudieron consultar las evaluaciones."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(evaluaciones)

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response(
                {"detail": "La evaluación debe enviarse como un objeto JSON."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            resultado = get_evaluaciones_collection().insert_one(request.data)
        except ImproperlyConfigured as error:
            logger.error("MongoDB no está configurado: %s", error)
            return Response(
                {"detail": "El almacenamiento de evaluaciones no está configurado."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except PyMongoError:
            logger.exception("No se pudo guardar la evaluación en MongoDB.")
            return Response(
                {"detail": "No se pudo guardar la evaluación."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {"id": str(resultado.inserted_id)},
            status=status.HTTP_201_CREATED,
        )


class ReporteGerencialView(APIView):
    permission_classes = [IsAuthenticated, IsGerencia]

    def get(self, request):
        try:
            evaluaciones = list(
                get_evaluaciones_collection().find({}, {"_id": 0})
            )
            reporte = crear_reporte_gerencial(evaluaciones)
            get_reportes_collection().replace_one(
                {"periodo": reporte["periodo"]},
                reporte,
                upsert=True,
            )
        except ImproperlyConfigured as error:
            logger.error("MongoDB no está configurado: %s", error)
            return Response(
                {"detail": "El almacenamiento de evaluaciones no está configurado."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except PyMongoError:
            logger.exception("No se pudo consultar o guardar el reporte en MongoDB.")
            return Response(
                {"detail": "No se pudo generar el reporte gerencial."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(reporte)
