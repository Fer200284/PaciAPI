from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import SolicitudDeExamenesViewSet

router = DefaultRouter()
router.register(r'solicitud-de-examenes', SolicitudDeExamenesViewSet, basename='solicitud-de-examenes')

urlpatterns = [
    path('', include(router.urls)),
]
