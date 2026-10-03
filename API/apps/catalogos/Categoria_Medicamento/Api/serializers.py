from rest_framework import serializers
from ..models import CategoriaMedicamento

class CategoriaMedicamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaMedicamento
        fields = "__all__"
