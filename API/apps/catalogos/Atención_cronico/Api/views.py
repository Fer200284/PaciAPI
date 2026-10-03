from rest_framework import viewsets
from ..models import AtencionCronico
from .serializers import AtencionCronicoSerializer

class AtencionCronicoViewSet(viewsets.ModelViewSet):
    queryset = AtencionCronico.objects.all()
    serializer_class = AtencionCronicoSerializer
