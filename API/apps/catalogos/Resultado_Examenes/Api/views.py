from rest_framework import viewsets
from ..models import ResultadosExamenes
from .serializers import ResultadosExamenesSerializer

class ResultadosExamenesViewSet(viewsets.ModelViewSet):
    queryset = ResultadosExamenes.objects.all()
    serializer_class = ResultadosExamenesSerializer
