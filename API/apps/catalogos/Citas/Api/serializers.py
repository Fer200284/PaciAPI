from rest_framework import serializers

from ..models import Citas


class CitasSerializer(serializers.ModelSerializer):
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
        )
        read_only_fields = fields
