from rest_framework import viewsets
from ..models import TipoEntrada
from .serializers import TipoEntradaSerializer

class TipoEntradaViewSet(viewsets.ModelViewSet):
    queryset = TipoEntrada.objects.all()
    serializer_class = TipoEntradaSerializer
