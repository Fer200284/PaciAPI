from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import TipoSalidaViewSet

router = DefaultRouter()
router.register(r'tipo-salida', TipoSalidaViewSet, basename='tipo-salida')

urlpatterns = [
    path('', include(router.urls)),
]
