from rest_framework import serializers
from apps.catalogos.patient_scope import PatientOwnedRelationsSerializerMixin
from ..models import DetalleTratamiento

class DetalleTratamientoSerializer(
    PatientOwnedRelationsSerializerMixin,
    serializers.ModelSerializer,
):
    patient_owned_fields = {
        "id_tratamiento": (
            "id_atencion_cronico__id_paciente_patologia__"
            "id_paciente__usuario"
        ),
    }

    class Meta:
        model = DetalleTratamiento
        fields = "__all__"
