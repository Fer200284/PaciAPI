from rest_framework import serializers
from ..models import PacientePatologia

class PacientePatologiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PacientePatologia
        fields = "__all__"
