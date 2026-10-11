from rest_framework import serializers
from ..models import Tratamiento

class TratamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tratamiento
        fields = "__all__"

    def validate_id_atencion_cronico(self, value):
        if (
            self.instance
            and self.instance.id_atencion_cronico_id == value.pk
        ):
            return value

        tratamiento_existente = Tratamiento.objects.filter(
            id_atencion_cronico=value
        ).exists()
        if tratamiento_existente:
            raise serializers.ValidationError(
                "Ya existe un tratamiento para esta atención. Agregue los medicamentos como detalles de ese tratamiento."
            )
        return value
