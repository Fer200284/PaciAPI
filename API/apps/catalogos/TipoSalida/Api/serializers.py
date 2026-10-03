from rest_framework import serializers
from ..models import TipoSalida

class TipoSalidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoSalida
        fields = "__all__"
