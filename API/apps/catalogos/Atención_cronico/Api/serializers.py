from rest_framework import serializers
from ..models import AtencionCronico

class AtencionCronicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AtencionCronico
        fields = "__all__"
