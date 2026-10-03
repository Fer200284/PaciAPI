import mimetypes
from pathlib import Path

from django.contrib import admin
from django.http import FileResponse, Http404, JsonResponse
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / 'FRONTEND'


def serve_frontend_page(request, filename):
    file_path = FRONTEND_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise Http404(f'Archivo no encontrado: {filename}')
    return FileResponse(file_path.open('rb'), content_type='text/html')


def serve_frontend_asset(request, path):
    file_path = FRONTEND_DIR / path
    if not file_path.exists() or not file_path.is_file():
        raise Http404(f'Archivo no encontrado: {path}')
    content_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(file_path.open('rb'), content_type=content_type or 'application/octet-stream')


def health_check(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('health/', health_check, name='health'),
    path('admin/', admin.site.urls),

    # Seguridad
    path('api/', include('apps.Seguridad.urls')),

    # APIs de catálogo
    path('api/', include('apps.catalogos.urls')),

    # Frontend estático
    path('', serve_frontend_page, {'filename': 'index.html'}, name='home'),
    path('login/', serve_frontend_page, {'filename': 'login.html'}, name='login'),
    path('login.html', serve_frontend_page, {'filename': 'login.html'}),
    re_path(r'^(?P<path>.*\.(?:css|js|png|jpg|jpeg|svg|gif|webp|ico|woff|woff2|ttf|eot))$', serve_frontend_asset),

    # Endpoints para Swagger y Redoc
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]