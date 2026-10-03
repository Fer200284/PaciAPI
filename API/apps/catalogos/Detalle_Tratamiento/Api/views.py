from rest_framework import viewsets
from ..models import DetalleTratamiento
from .serializers import DetalleTratamientoSerializer

class DetalleTratamientoViewSet(viewsets.ModelViewSet):
    queryset = DetalleTratamiento.objects.all()
    serializer_class = DetalleTratamientoSerializer
