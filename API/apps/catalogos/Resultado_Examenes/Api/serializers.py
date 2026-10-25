from rest_framework import serializers
from apps.catalogos.patient_scope import PatientOwnedRelationsSerializerMixin
from ..models import ResultadosExamenes

class ResultadosExamenesSerializer(
    PatientOwnedRelationsSerializerMixin,
    serializers.ModelSerializer,
):
    patient_owned_fields = {
        "id_solicitud_examen": (
            "id_atencion_cronico__id_paciente_patologia__"
            "id_paciente__usuario"
        ),
    }

    class Meta:
        model = ResultadosExamenes
        fields = "__all__"
