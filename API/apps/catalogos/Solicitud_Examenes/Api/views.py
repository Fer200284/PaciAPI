from rest_framework import viewsets
from ..models import SolicitudDeExamenes
from .serializers import SolicitudDeExamenesSerializer

class SolicitudDeExamenesViewSet(viewsets.ModelViewSet):
    queryset = SolicitudDeExamenes.objects.all()
    serializer_class = SolicitudDeExamenesSerializer
