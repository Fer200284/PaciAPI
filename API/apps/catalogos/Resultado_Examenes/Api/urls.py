from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ResultadosExamenesViewSet

router = DefaultRouter()
router.register(r'resultados-examenes', ResultadosExamenesViewSet, basename='resultados-examenes')

urlpatterns = [
    path('', include(router.urls)),
]
