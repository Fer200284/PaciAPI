from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    # Estado de la API
    path("health/", health_check, name="health"),

    # Administración de Django
    path("admin/", admin.site.urls),

    # API de Seguridad
    path("api/", include("apps.Seguridad.urls")),

    # API de Catálogos
    path("api/", include("apps.catalogos.urls")),

    # Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # Redoc
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]