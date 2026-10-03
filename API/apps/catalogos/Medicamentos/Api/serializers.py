from rest_framework import serializers
from ..models import Medicamentos

class MedicamentosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicamentos
        fields = "__all__"
