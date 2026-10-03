from rest_framework import viewsets
from ..models import PacientePatologia
from .serializers import PacientePatologiaSerializer

class PacientePatologiaViewSet(viewsets.ModelViewSet):
    queryset = PacientePatologia.objects.all()
    serializer_class = PacientePatologiaSerializer
