from django.contrib import admin
from apps.catalogos.Resultado_Examenes.models import ResultadosExamenes


@admin.register(ResultadosExamenes)
class ResultadoExamenAdmin(admin.ModelAdmin):
  list_display = (
      'id',
      'id_solicitud_examen',
      'valor_resultado',
      'fecha_resultado',
  )
  list_filter = ('fecha_resultado',)