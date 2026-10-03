from rest_framework import serializers
from ..models import TipoEntrada

class TipoEntradaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEntrada
        fields = "__all__"
