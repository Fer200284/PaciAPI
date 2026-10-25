from rest_framework import serializers
from apps.catalogos.patient_scope import PatientOwnedRelationsSerializerMixin
from ..models import AtencionCronico

class AtencionCronicoSerializer(
    PatientOwnedRelationsSerializerMixin,
    serializers.ModelSerializer,
):
    patient_owned_fields = {
        "id_paciente_patologia": "id_paciente__usuario",
    }

    class Meta:
        model = AtencionCronico
        fields = "__all__"

    def validate(self, attrs):
        attrs = super().validate(attrs)
        fecha = attrs.get(
            "fecha_proxima_cita",
            getattr(self.instance, "fecha_proxima_cita", None),
        )
        hora = attrs.get(
            "hora_proxima_cita",
            getattr(self.instance, "hora_proxima_cita", None),
        )
        if hora and not fecha:
            raise serializers.ValidationError({
                "fecha_proxima_cita": "Se requiere la fecha para guardar la hora de la próxima cita."
            })
        return attrs
