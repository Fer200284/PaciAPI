from django.utils import timezone
from rest_framework import serializers

from apps.catalogos.Atención_cronico.models import AtencionCronico
from ..models import Citas


class CitasSerializer(serializers.ModelSerializer):
    id_atencion = serializers.SerializerMethodField()
    fecha_hora_llegada = serializers.SerializerMethodField()
    fecha_hora_inicio_consulta = serializers.SerializerMethodField()
    fecha_hora_fin_consulta = serializers.SerializerMethodField()

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
            "fecha_hora_llegada",
            "fecha_hora_inicio_consulta",
            "fecha_hora_fin_consulta",
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

    def get_fecha_hora_llegada(self, cita):
        atencion = self._atencion(cita)
        return atencion.fecha_hora_llegada if atencion else None

    def get_fecha_hora_inicio_consulta(self, cita):
        atencion = self._atencion(cita)
        return atencion.fecha_hora_inicio_consulta if atencion else None

    def get_fecha_hora_fin_consulta(self, cita):
        atencion = self._atencion(cita)
        return atencion.fecha_hora_fin_consulta if atencion else None
