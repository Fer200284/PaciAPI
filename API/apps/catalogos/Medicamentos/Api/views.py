from rest_framework import viewsets
from ..models import Medicamentos
from .serializers import MedicamentosSerializer

class MedicamentosViewSet(viewsets.ModelViewSet):
    queryset = Medicamentos.objects.all()
    serializer_class = MedicamentosSerializer
