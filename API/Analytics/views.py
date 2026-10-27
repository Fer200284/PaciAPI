import logging

from django.core.exceptions import ImproperlyConfigured
from bson import ObjectId
from pymongo.errors import PyMongoError
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.catalogos.patient_scope import is_patient_user
from apps.catalogos.Pacientes.models import Pacientes
from apps.Seguridad.Usuarios.models import User
from .serializers import ActualizarEncuestaSerializer, EncuestaSerializer
from .services import (
    actualizar_encuesta,
    eliminar_encuesta,
    guardar_encuesta,
    listar_encuestas,
    obtener_encuesta,
)


logger = logging.getLogger(__name__)


def es_gerencia(user):
    return getattr(user, "rol", None) == User.Roles.GERENCIA


def filtro_encuestas_usuario(user):
    paciente_id = Pacientes.objects.filter(usuario=user).values_list(
        "pk",
        flat=True,
    ).first()
    if paciente_id is None:
        raise PermissionDenied(
            "La cuenta no está vinculada a una ficha de paciente."
        )
    return {"id_paciente": paciente_id}


def documento_para_respuesta(documento):
    documento["id"] = str(documento.pop("_id"))
    return documento


def validar_id_mongo(encuesta_id):
    if not ObjectId.is_valid(encuesta_id):
        raise NotFound("No se encontró la encuesta solicitada.")
    return ObjectId(encuesta_id)


class EncuestasView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EncuestaSerializer

    def get(self, request):
        if es_gerencia(request.user):
            filtro = {}
        elif is_patient_user(request.user):
            filtro = filtro_encuestas_usuario(request.user)
        else:
            raise PermissionDenied(
                "Solo Paciente o Gerencia puede consultar encuestas."
            )

        try:
            encuestas = listar_encuestas(filtro)
        except ImproperlyConfigured as error:
            logger.error("MongoDB no está configurado: %s", error)
            return Response(
                {"detail": "El almacenamiento de encuestas no está configurado."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except PyMongoError:
            logger.exception("No se pudieron consultar las encuestas en MongoDB.")
            return Response(
                {"detail": "No se pudieron consultar las encuestas."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response([
            documento_para_respuesta(encuesta)
            for encuesta in encuestas
        ])

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


class EncuestaDetalleView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ActualizarEncuestaSerializer

    def get_filtro(self, request, encuesta_id):
        mongo_id = validar_id_mongo(encuesta_id)
        if is_patient_user(request.user):
            return {"_id": mongo_id, **filtro_encuestas_usuario(request.user)}
        if es_gerencia(request.user):
            return {"_id": mongo_id}
        raise PermissionDenied(
            "Solo Paciente o Gerencia puede consultar encuestas."
        )

    def get(self, request, encuesta_id):
        filtro = self.get_filtro(request, encuesta_id)
        try:
            encuesta = obtener_encuesta(filtro)
        except ImproperlyConfigured as error:
            logger.error("MongoDB no está configurado: %s", error)
            return Response(
                {"detail": "El almacenamiento de encuestas no está configurado."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except PyMongoError:
            logger.exception("No se pudo consultar la encuesta en MongoDB.")
            return Response(
                {"detail": "No se pudo consultar la encuesta."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if encuesta is None:
            raise NotFound("No se encontró la encuesta solicitada.")
        return Response(documento_para_respuesta(encuesta))

    def put(self, request, encuesta_id):
        return self.actualizar(request, encuesta_id)

    def patch(self, request, encuesta_id):
        return self.actualizar(request, encuesta_id)

    def actualizar(self, request, encuesta_id):
        if not is_patient_user(request.user):
            raise PermissionDenied(
                "Solo el paciente propietario puede editar su encuesta."
            )

        filtro = {
            "_id": validar_id_mongo(encuesta_id),
            **filtro_encuestas_usuario(request.user),
        }
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        cambios = dict(serializer.validated_data)
        try:
            resultado = actualizar_encuesta(filtro, cambios)
            if not resultado.matched_count:
                raise NotFound("No se encontró la encuesta solicitada.")
            encuesta = obtener_encuesta(filtro)
        except ImproperlyConfigured as error:
            logger.error("MongoDB no está configurado: %s", error)
            return Response(
                {"detail": "El almacenamiento de encuestas no está configurado."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except PyMongoError:
            logger.exception("No se pudo actualizar la encuesta en MongoDB.")
            return Response(
                {"detail": "No se pudo actualizar la encuesta."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if encuesta is None:
            raise NotFound("No se encontró la encuesta solicitada.")
        return Response(documento_para_respuesta(encuesta))

    def delete(self, request, encuesta_id):
        if not is_patient_user(request.user):
            raise PermissionDenied(
                "Solo el paciente propietario puede eliminar su encuesta."
            )

        filtro = {
            "_id": validar_id_mongo(encuesta_id),
            **filtro_encuestas_usuario(request.user),
        }
        try:
            resultado = eliminar_encuesta(filtro)
        except ImproperlyConfigured as error:
            logger.error("MongoDB no está configurado: %s", error)
            return Response(
                {"detail": "El almacenamiento de encuestas no está configurado."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except PyMongoError:
            logger.exception("No se pudo eliminar la encuesta en MongoDB.")
            return Response(
                {"detail": "No se pudo eliminar la encuesta."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if not resultado.deleted_count:
            raise NotFound("No se encontró la encuesta solicitada.")
        return Response(status=status.HTTP_204_NO_CONTENT)
