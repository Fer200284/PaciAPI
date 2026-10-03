from django.contrib import admin
from apps.catalogos.Solicitud_Examenes.models import SolicitudDeExamenes


@admin.register(SolicitudDeExamenes)
class SolicitudDeExamenesAdmin(admin.ModelAdmin):
  list_display = (
      'id',
      'id_examen_de_laboratorio',
      'id_atencion_cronico',
      'fecha_de_envio',
  )
  list_filter = ('fecha_de_envio',)