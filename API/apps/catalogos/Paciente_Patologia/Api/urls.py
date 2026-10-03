from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import PacientePatologiaViewSet

router = DefaultRouter()
router.register(r'paciente-patologia', PacientePatologiaViewSet, basename='paciente-patologia')

urlpatterns = [
    path('', include(router.urls)),
]
