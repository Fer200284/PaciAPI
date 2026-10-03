from django.contrib import admin
from apps.catalogos.Examenes_Laboratorio.models import ExamenesDeLaboratorio


@admin.register(ExamenesDeLaboratorio)
class ExamenesDeLaboratorioAdmin(admin.ModelAdmin):
  list_display = (
      'id',
      'nombre_examen',
      'unidad_medida',
      'valor_referencia',
      'estado',
  )
  search_fields = ('nombre_examen',)
  list_filter = ('estado',)