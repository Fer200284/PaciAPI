from rest_framework import serializers
from ..models import Especialidades

class EspecialidadesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidades
        fields = "__all__"
