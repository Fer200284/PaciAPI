from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import AtencionCronicoViewSet

router = DefaultRouter()
router.register(r'atencion-cronico', AtencionCronicoViewSet, basename='atencion-cronico')

urlpatterns = [
    path('', include(router.urls)),
]
