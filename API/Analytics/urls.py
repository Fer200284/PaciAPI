from django.urls import path

from .views import EncuestasView


urlpatterns = [
    path("analytics/encuestas/", EncuestasView.as_view(), name="analytics-encuestas"),
]
