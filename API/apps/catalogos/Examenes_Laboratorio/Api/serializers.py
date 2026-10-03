from rest_framework import serializers
from ..models import ExamenesDeLaboratorio

class ExamenesDeLaboratorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamenesDeLaboratorio
        fields = "__all__"
