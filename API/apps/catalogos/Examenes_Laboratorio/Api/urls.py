from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ExamenesDeLaboratorioViewSet

router = DefaultRouter()
router.register(r'examenes-de-laboratorio', ExamenesDeLaboratorioViewSet, basename='examenes-de-laboratorio')

urlpatterns = [
    path('', include(router.urls)),
]
