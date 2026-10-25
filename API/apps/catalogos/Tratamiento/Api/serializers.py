from rest_framework import serializers
from apps.catalogos.patient_scope import (
    PatientOwnedRelationsSerializerMixin,
    is_patient_user,
)
from ..models import Tratamiento

class TratamientoSerializer(
    PatientOwnedRelationsSerializerMixin,
    serializers.ModelSerializer,
):
    patient_owned_fields = {
        "id_atencion_cronico": (
            "id_paciente_patologia__id_paciente__usuario"
        ),
    }

    class Meta:
        model = Tratamiento
        fields = "__all__"

    def validate_id_atencion_cronico(self, value):
        request = self.context.get("request")
        if (
            request
            and is_patient_user(request.user)
            and not value.__class__.objects.filter(
                pk=value.pk,
                id_paciente_patologia__id_paciente__usuario=request.user,
            ).exists()
        ):
            raise serializers.ValidationError(
                "No puedes utilizar información de otro paciente."
            )

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
