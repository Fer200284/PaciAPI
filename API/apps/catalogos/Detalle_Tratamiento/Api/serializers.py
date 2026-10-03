from rest_framework import serializers
from ..models import DetalleTratamiento

class DetalleTratamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleTratamiento
        fields = "__all__"
