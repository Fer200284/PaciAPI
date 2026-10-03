from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import PatologiasCronicasViewSet

router = DefaultRouter()
router.register(r'patologias-cronicas', PatologiasCronicasViewSet, basename='patologias-cronicas')

urlpatterns = [
    path('', include(router.urls)),
]
