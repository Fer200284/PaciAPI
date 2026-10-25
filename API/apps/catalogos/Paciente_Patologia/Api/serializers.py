from rest_framework import serializers
from apps.catalogos.patient_scope import PatientOwnedRelationsSerializerMixin
from ..models import PacientePatologia

class PacientePatologiaSerializer(
    PatientOwnedRelationsSerializerMixin,
    serializers.ModelSerializer,
):
    patient_owned_fields = {"id_paciente": "usuario"}

    class Meta:
        model = PacientePatologia
        fields = "__all__"
