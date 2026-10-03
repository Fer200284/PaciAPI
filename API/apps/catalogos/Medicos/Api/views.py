from rest_framework import viewsets
from ..models import Medicos
from .serializers import MedicosSerializer

class MedicosViewSet(viewsets.ModelViewSet):
    queryset = Medicos.objects.all()
    serializer_class = MedicosSerializer
