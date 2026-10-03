from rest_framework import viewsets
from ..models import Sector
from .serializers import SectorSerializer

class SectorViewSet(viewsets.ModelViewSet):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
