from django.contrib import admin
from apps.catalogos.Medicamentos. models import Medicamentos


@admin.register(Medicamentos)
class MedicamentosAdmin(admin.ModelAdmin):
  list_display = (
      'id',
      'nombre_medicamento',
      'presentacion',
      'concentracion',
      'id_categoria_medicamento',
      'estado',
  )
  search_fields = ('nombre_medicamento',)
  list_filter = ('estado', 'id_categoria_medicamento')