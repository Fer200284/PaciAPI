import secrets
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.catalogos.patient_scope import is_patient_user
from apps.catalogos.Atención_cronico.models import AtencionCronico
from apps.catalogos.Detalle_Tratamiento.models import DetalleTratamiento
from apps.catalogos.Pacientes.models import Pacientes
from apps.catalogos.Resultado_Examenes.models import ResultadosExamenes
from apps.catalogos.Solicitud_Examenes.models import SolicitudDeExamenes
from apps.Seguridad.Usuarios.models import GerenciaInvitationCode, User
from .serializers import (
    GerenciaInvitationCodeSerializer,
    MobileSummarySerializer,
    UserSerializer,
)


GERENCIA_CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def is_administrator(user):
    return (
        user.is_authenticated
        and getattr(user, 'rol', None) == User.Roles.ADMINISTRADOR
    )


class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_patient_user(self.request.user):
            return queryset.filter(pk=self.request.user.pk)
        return queryset

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get', 'post'],
        permission_classes=[IsAuthenticated],
        url_path='invitaciones-gerencia',
    )
    def invitaciones_gerencia(self, request):
        if not is_administrator(request.user):
            raise PermissionDenied(
                'Solo Administrador puede gestionar invitaciones de Gerencia.'
            )

        if request.method == 'GET':
            invitations = GerenciaInvitationCode.objects.select_related(
                'created_by',
                'used_by',
            )
            serializer = GerenciaInvitationCodeSerializer(
                invitations,
                many=True,
            )
            return Response(serializer.data)

        now = timezone.now()
        for _ in range(5):
            code = ''.join(
                secrets.choice(GERENCIA_CODE_ALPHABET)
                for _ in range(16)
            )
            if GerenciaInvitationCode.objects.filter(code=code).exists():
                continue
            invitation = GerenciaInvitationCode.objects.create(
                code=code,
                created_by=request.user,
                expires_at=now + timedelta(hours=24),
            )
            serializer = GerenciaInvitationCodeSerializer(invitation)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        raise ValidationError(
            'No se pudo generar un código único. Intente nuevamente.'
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        serializer_class=MobileSummarySerializer,
        url_path='resumen-movil',
    )
    def resumen_movil(self, request):
        """Return current patient data; refetch to observe changes or removals."""
        if not is_patient_user(request.user):
            raise PermissionDenied(
                "Este resumen está disponible únicamente para pacientes."
            )
        if not Pacientes.objects.filter(usuario=request.user).exists():
            raise ValidationError(
                "La cuenta todavía no está vinculada a una ficha de paciente."
            )

        appointment = (
            AtencionCronico.objects.filter(
                id_paciente_patologia__id_paciente__usuario=request.user,
                fecha_proxima_cita__gte=timezone.localdate(),
            )
            .order_by("fecha_proxima_cita", "hora_proxima_cita", "pk")
            .values(
                "id",
                "fecha_proxima_cita",
                "hora_proxima_cita",
                "id_medico__nombre",
                "id_medico__apellidos",
                "id_paciente_patologia__id_patologia_cronica__nombre_patologia",
            )
            .first()
        )
        if appointment is not None:
            appointment = {
                "id": appointment["id"],
                "fecha": appointment["fecha_proxima_cita"],
                "hora": appointment["hora_proxima_cita"],
                "medico": {
                    "nombre": appointment["id_medico__nombre"],
                    "apellidos": appointment["id_medico__apellidos"],
                },
                "patologia": appointment[
                    "id_paciente_patologia__id_patologia_cronica__nombre_patologia"
                ],
            }

        medication_rows = list(
            DetalleTratamiento.objects.filter(
                id_tratamiento__id_atencion_cronico__id_paciente_patologia__id_paciente__usuario=request.user
            )
            .order_by("pk")
            .values(
                "id",
                "cantidad_entregada",
                "indicacion",
                "id_medicamento",
                "id_medicamento__nombre_medicamento",
                "id_medicamento__presentacion",
                "id_medicamento__concentracion",
                "id_medicamento__estado",
                "id_tratamiento__fecha_tratamiento",
                "id_tratamiento__observaciones",
            )
        )
        medication_details = [{
            "id": medication["id"],
            "medicamento_id": medication["id_medicamento"],
            "nombre": medication["id_medicamento__nombre_medicamento"],
            "presentacion": medication["id_medicamento__presentacion"],
            "concentracion": medication["id_medicamento__concentracion"],
            "activo": medication["id_medicamento__estado"],
            "cantidad_entregada": medication["cantidad_entregada"],
            "indicacion": medication["indicacion"],
            "fecha_tratamiento": medication["id_tratamiento__fecha_tratamiento"],
            "observaciones": medication["id_tratamiento__observaciones"],
        } for medication in medication_rows]

        exam_rows = list(
            SolicitudDeExamenes.objects.filter(
                id_atencion_cronico__id_paciente_patologia__id_paciente__usuario=request.user
            )
            .order_by("-fecha_de_envio", "pk")
            .values(
                "id",
                "id_examen_de_laboratorio",
                "id_examen_de_laboratorio__nombre_examen",
                "id_examen_de_laboratorio__unidad_medida",
                "id_examen_de_laboratorio__valor_referencia",
                "id_examen_de_laboratorio__estado",
                "indicaciones",
                "fecha_de_envio",
            )
        )
        exam_request_ids = [exam["id"] for exam in exam_rows]
        results_by_request = {}
        if exam_request_ids:
            results = ResultadosExamenes.objects.filter(
                id_solicitud_examen__in=exam_request_ids
            ).order_by("fecha_resultado", "pk").values(
                "id",
                "id_solicitud_examen",
                "valor_resultado",
                "interpretacion",
                "fecha_resultado",
            )
            for result in results:
                results_by_request.setdefault(
                    result["id_solicitud_examen"], []
                ).append({
                    "id": result["id"],
                    "valor_resultado": result["valor_resultado"],
                    "interpretacion": result["interpretacion"],
                    "fecha_resultado": result["fecha_resultado"],
                })

        exam_requests = [{
            "id": exam["id"],
            "examen_id": exam["id_examen_de_laboratorio"],
            "nombre": exam["id_examen_de_laboratorio__nombre_examen"],
            "unidad_medida": exam["id_examen_de_laboratorio__unidad_medida"],
            "valor_referencia": exam["id_examen_de_laboratorio__valor_referencia"],
            "activo": exam["id_examen_de_laboratorio__estado"],
            "indicaciones": exam["indicaciones"],
            "fecha_solicitud": exam["fecha_de_envio"],
            "resultados": results_by_request.get(exam["id"], []),
        } for exam in exam_rows]

        return Response({
            "proxima_cita": appointment,
            "medicamentos": medication_details,
            "examenes_solicitados": exam_requests,
        })