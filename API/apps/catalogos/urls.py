from django.urls import include, path

urlpatterns = [
    path('', include('apps.catalogos.Pacientes.Api.urls')),
    path('', include('apps.catalogos.Medicos.Api.urls')),
    path('', include('apps.catalogos.Especialidades.Api.urls')),
    path('', include('apps.catalogos.Medicamentos.Api.urls')),
    path('', include('apps.catalogos.Categoria_Medicamento.Api.urls')),
    path('', include('apps.catalogos.Detalle_Tratamiento.Api.urls')),
    path('', include('apps.catalogos.Examenes_Laboratorio.Api.urls')),
    path('', include('apps.catalogos.Solicitud_Examenes.Api.urls')),
    path('', include('apps.catalogos.Resultado_Examenes.Api.urls')),
    path('', include('apps.catalogos.Tratamiento.Api.urls')),
    path('', include('apps.catalogos.Paciente_Patologia.Api.urls')),
    path('', include('apps.catalogos.Patologias_Cronicas.Api.urls')),
    path('', include('apps.catalogos.Sector.Api.urls')),
    path('', include('apps.catalogos.TipoEntrada.Api.urls')),
    path('', include('apps.catalogos.TipoSalida.Api.urls')),
    path('', include('apps.catalogos.Atención_cronico.Api.urls')),
]
