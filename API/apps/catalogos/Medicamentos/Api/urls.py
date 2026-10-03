from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import MedicamentosViewSet

router = DefaultRouter()
router.register(r'medicamentos', MedicamentosViewSet, basename='medicamentos')

urlpatterns = [
    path('', include(router.urls)),
]
