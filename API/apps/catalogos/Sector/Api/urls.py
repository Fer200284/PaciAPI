from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import SectorViewSet

router = DefaultRouter()
router.register(r'sector', SectorViewSet, basename='sector')

urlpatterns = [
    path('', include(router.urls)),
]
