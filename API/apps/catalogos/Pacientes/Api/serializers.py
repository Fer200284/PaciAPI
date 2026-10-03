from rest_framework import serializers
from ..models import Pacientes

class PacientesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pacientes
        fields = '__all__'  # Esto incluye todos los campos de tu modelo automáticamente