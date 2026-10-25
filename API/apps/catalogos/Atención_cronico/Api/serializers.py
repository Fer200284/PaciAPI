from rest_framework import serializers
from ..models import AtencionCronico

class AtencionCronicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AtencionCronico
        fields = "__all__"

    def validate(self, attrs):
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
