from django.urls import path

from .views import AnalyticsAtencionesView, EncuestaDetalleView, EncuestasView


urlpatterns = [
    path("analytics/encuestas/", EncuestasView.as_view(), name="analytics-encuestas"),
    path(
        "analytics/atenciones/",
        AnalyticsAtencionesView.as_view(),
        name="analytics-atenciones",
    ),
    path(
        "analytics/encuestas/<str:encuesta_id>/",
        EncuestaDetalleView.as_view(),
        name="analytics-encuesta-detalle",
    ),
]
