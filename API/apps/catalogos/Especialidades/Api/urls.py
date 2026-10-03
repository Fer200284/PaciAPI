from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import EspecialidadesViewSet

router = DefaultRouter()
router.register(r'especialidades', EspecialidadesViewSet, basename='especialidades')

urlpatterns = [
    path('', include(router.urls)),
]
