from rest_framework import viewsets
from ..models import TipoSalida
from .serializers import TipoSalidaSerializer

class TipoSalidaViewSet(viewsets.ModelViewSet):
    queryset = TipoSalida.objects.all()
    serializer_class = TipoSalidaSerializer
