from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import TipoEntradaViewSet

router = DefaultRouter()
router.register(r'tipo-entrada', TipoEntradaViewSet, basename='tipo-entrada')

urlpatterns = [
    path('', include(router.urls)),
]
