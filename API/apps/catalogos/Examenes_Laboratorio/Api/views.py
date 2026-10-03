from rest_framework import viewsets
from ..models import ExamenesDeLaboratorio
from .serializers import ExamenesDeLaboratorioSerializer

class ExamenesDeLaboratorioViewSet(viewsets.ModelViewSet):
    queryset = ExamenesDeLaboratorio.objects.all()
    serializer_class = ExamenesDeLaboratorioSerializer
