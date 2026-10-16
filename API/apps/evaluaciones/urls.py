from django.urls import path

from .views import EvaluacionesView


urlpatterns = [
    path("evaluaciones/", EvaluacionesView.as_view(), name="evaluaciones"),
]
