from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import MedicosViewSet

router = DefaultRouter()
router.register(r'medicos', MedicosViewSet, basename='medicos')

urlpatterns = [
    path('', include(router.urls)),
]
