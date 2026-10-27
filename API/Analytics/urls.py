from django.urls import path

from .views import EncuestaDetalleView, EncuestasView


urlpatterns = [
    path("analytics/encuestas/", EncuestasView.as_view(), name="analytics-encuestas"),
    path(
        "analytics/encuestas/<str:encuesta_id>/",
        EncuestaDetalleView.as_view(),
        name="analytics-encuesta-detalle",
    ),
]
