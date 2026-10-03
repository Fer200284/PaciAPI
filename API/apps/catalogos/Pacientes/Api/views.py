from rest_framework import viewsets
from ..models import Pacientes
from .serializers import PacientesSerializer

class PacientesViewSet(viewsets.ModelViewSet):
    queryset = Pacientes.objects.all()
    serializer_class = PacientesSerializer