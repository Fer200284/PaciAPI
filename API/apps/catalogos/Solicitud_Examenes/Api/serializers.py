from rest_framework import serializers
from apps.catalogos.patient_scope import PatientOwnedRelationsSerializerMixin
from ..models import SolicitudDeExamenes

class SolicitudDeExamenesSerializer(
    PatientOwnedRelationsSerializerMixin,
    serializers.ModelSerializer,
):
    patient_owned_fields = {
        "id_atencion_cronico": (
            "id_paciente_patologia__id_paciente__usuario"
        ),
    }

    class Meta:
        model = SolicitudDeExamenes
        fields = "__all__"
