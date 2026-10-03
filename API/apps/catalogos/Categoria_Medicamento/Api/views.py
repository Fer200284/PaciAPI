from rest_framework import viewsets
from ..models import CategoriaMedicamento
from .serializers import CategoriaMedicamentoSerializer

class CategoriaMedicamentoViewSet(viewsets.ModelViewSet):
    queryset = CategoriaMedicamento.objects.all()
    serializer_class = CategoriaMedicamentoSerializer
