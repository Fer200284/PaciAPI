from rest_framework import viewsets
from ..models import Especialidades
from .serializers import EspecialidadesSerializer

class EspecialidadesViewSet(viewsets.ModelViewSet):
    queryset = Especialidades.objects.all()
    serializer_class = EspecialidadesSerializer
