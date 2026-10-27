from datetime import datetime

from rest_framework import serializers


class EncuestaSerializer(serializers.Serializer):
    id_encuesta = serializers.IntegerField(min_value=1)
    id_fecha = serializers.IntegerField(min_value=10000101, max_value=99991231)
    id_paciente = serializers.IntegerField(min_value=1)
    id_patologia = serializers.IntegerField(min_value=1)
    puntuacion_general = serializers.IntegerField(min_value=1, max_value=5)
    score_atencion_medica = serializers.IntegerField(min_value=1, max_value=5)
    tiempo_espera_minutos = serializers.IntegerField(min_value=0)
    score_trato_personal = serializers.IntegerField(min_value=1, max_value=5)
    score_consulta_doctor = serializers.IntegerField(min_value=1, max_value=5)
    resolucion_dudas_val = serializers.IntegerField(min_value=0, max_value=1)

    def validate_id_fecha(self, value):
        fecha = str(value)
        if len(fecha) != 8:
            raise serializers.ValidationError(
                "La fecha debe tener el formato AAAAMMDD."
            )
        try:
            datetime.strptime(fecha, "%Y%m%d")
        except ValueError as error:
            raise serializers.ValidationError(
                "La fecha AAAAMMDD no es válida."
            ) from error
        return value
