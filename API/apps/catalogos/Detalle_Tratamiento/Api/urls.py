from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import DetalleTratamientoViewSet

router = DefaultRouter()
router.register(r'detalle-tratamiento', DetalleTratamientoViewSet, basename='detalle-tratamiento')

urlpatterns = [
    path('', include(router.urls)),
]
