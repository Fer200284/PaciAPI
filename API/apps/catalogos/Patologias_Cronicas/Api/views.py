from rest_framework import viewsets
from ..models import PatologiasCronicas
from .serializers import PatologiasCronicasSerializer

class PatologiasCronicasViewSet(viewsets.ModelViewSet):
    queryset = PatologiasCronicas.objects.all()
    serializer_class = PatologiasCronicasSerializer
