from rest_framework import serializers


class EncuestaSerializer(serializers.Serializer):
    id_encuesta = serializers.IntegerField(min_value=1)
    id_fecha = serializers.DateField(input_formats=["%Y-%m-%d"])
    id_paciente = serializers.IntegerField(min_value=1)
    id_patologia = serializers.IntegerField(min_value=1)
    puntuacion_general = serializers.IntegerField(min_value=1, max_value=5)
    score_atencion_medica = serializers.IntegerField(min_value=1, max_value=5)
    tiempo_espera_minutos = serializers.IntegerField(min_value=0)
    score_trato_personal = serializers.IntegerField(min_value=1, max_value=5)
    score_consulta_doctor = serializers.IntegerField(min_value=1, max_value=5)
    resolucion_dudas_val = serializers.IntegerField(min_value=0, max_value=1)
    comentario = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000,
    )


class ActualizarEncuestaSerializer(serializers.Serializer):
    puntuacion_general = serializers.IntegerField(
        min_value=1,
        max_value=5,
        required=False,
    )
    score_atencion_medica = serializers.IntegerField(
        min_value=1,
        max_value=5,
        required=False,
    )
    tiempo_espera_minutos = serializers.IntegerField(
        min_value=0,
        required=False,
    )
    score_trato_personal = serializers.IntegerField(
        min_value=1,
        max_value=5,
        required=False,
    )
    score_consulta_doctor = serializers.IntegerField(
        min_value=1,
        max_value=5,
        required=False,
    )
    resolucion_dudas_val = serializers.IntegerField(
        min_value=0,
        max_value=1,
        required=False,
    )
    comentario = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000,
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "Envía al menos un campo para actualizar."
            )
        return attrs
