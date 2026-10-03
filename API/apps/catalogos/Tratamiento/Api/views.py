from rest_framework import viewsets
from ..models import Tratamiento
from .serializers import TratamientoSerializer

class TratamientoViewSet(viewsets.ModelViewSet):
    queryset = Tratamiento.objects.all()
    serializer_class = TratamientoSerializer
