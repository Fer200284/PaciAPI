from django.urls import path

from .views import EvaluacionesView, ReporteGerencialView


urlpatterns = [
    path("evaluaciones/", EvaluacionesView.as_view(), name="evaluaciones"),
    path(
        "reportes-gerenciales/",
        ReporteGerencialView.as_view(),
        name="reportes-gerenciales",
    ),
]
