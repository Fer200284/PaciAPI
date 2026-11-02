from django.utils import timezone
from rest_framework import serializers

from apps.catalogos.Atención_cronico.models import AtencionCronico
from ..models import Citas


class CitasSerializer(serializers.ModelSerializer):
    id_atencion = serializers.SerializerMethodField()
    estado = serializers.SerializerMethodField()
    fecha_atencion_real = serializers.SerializerMethodField()

    class Meta:
        model = Citas
        fields = (
            "id",
            "id_paciente",
            "id_medico",
            "fecha_hora_cita",
            "estado",
            "fecha_atencion_real",
            "observaciones",
            "fecha_creacion",
            "id_atencion",
        )
        read_only_fields = fields

    def _atencion(self, cita):
        if hasattr(cita, "_atenciones_cita"):
            atenciones = cita._atenciones_cita
            if atenciones:
                return atenciones[0]
            return self._buscar_atencion_por_programacion(cita)

        return cita.atenciones.order_by("pk").first() or (
            self._buscar_atencion_por_programacion(cita)
        )

    def _buscar_atencion_por_programacion(self, cita):
        if hasattr(cita, "_atencion_programada"):
            return cita._atencion_programada

        fecha_hora_local = timezone.localtime(cita.fecha_hora_cita)
        cita._atencion_programada = AtencionCronico.objects.filter(
            id_paciente_patologia__id_paciente_id=cita.id_paciente_id,
            id_medico_id=cita.id_medico_id,
            fecha_proxima_cita=fecha_hora_local.date(),
            hora_proxima_cita=fecha_hora_local.time().replace(tzinfo=None),
        ).order_by("pk").first()
        return cita._atencion_programada

    def get_id_atencion(self, cita):
        atencion = self._atencion(cita)
        return atencion.pk if atencion else None

    def _es_cita_futura(self, cita):
        return (
            timezone.localtime(cita.fecha_hora_cita).date()
            > timezone.localdate()
        )

    def get_estado(self, cita):
        if (
            cita.estado == Citas.Estado.ASISTIO
            and self._es_cita_futura(cita)
        ):
            return Citas.Estado.PROGRAMADA
        return cita.estado

    def get_fecha_atencion_real(self, cita):
        if (
            cita.estado == Citas.Estado.ASISTIO
            and self._es_cita_futura(cita)
        ):
            return None
        return cita.fecha_atencion_real
