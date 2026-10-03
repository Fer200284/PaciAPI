from rest_framework import serializers
from ..models import ResultadosExamenes

class ResultadosExamenesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultadosExamenes
        fields = "__all__"
