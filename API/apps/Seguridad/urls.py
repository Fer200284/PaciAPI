from django.urls import include, path

urlpatterns = [
    path('', include('apps.Seguridad.Usuarios.Api.urls')),
]
