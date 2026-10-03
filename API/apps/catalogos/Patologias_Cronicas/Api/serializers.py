from rest_framework import serializers
from ..models import PatologiasCronicas

class PatologiasCronicasSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatologiasCronicas
        fields = "__all__"
