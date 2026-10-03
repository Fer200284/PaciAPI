from rest_framework import serializers
from ..models import SolicitudDeExamenes

class SolicitudDeExamenesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudDeExamenes
        fields = "__all__"
