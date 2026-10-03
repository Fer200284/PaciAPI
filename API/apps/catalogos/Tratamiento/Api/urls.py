from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import TratamientoViewSet

router = DefaultRouter()
router.register(r'tratamiento', TratamientoViewSet, basename='tratamiento')

urlpatterns = [
    path('', include(router.urls)),
]
