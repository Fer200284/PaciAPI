from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PacientesViewSet  # Como views.py está al lado, solo pones '.views'

router = DefaultRouter()
router.register(r'pacientes', PacientesViewSet, basename='pacientes')

urlpatterns = [
    path('', include(router.urls)),
]