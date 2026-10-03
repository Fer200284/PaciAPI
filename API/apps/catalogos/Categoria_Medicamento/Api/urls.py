from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import CategoriaMedicamentoViewSet

router = DefaultRouter()
router.register(r'categoria-medicamento', CategoriaMedicamentoViewSet, basename='categoria-medicamento')

urlpatterns = [
    path('', include(router.urls)),
]
