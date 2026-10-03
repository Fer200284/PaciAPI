from django.contrib import admin
from apps.catalogos.Categoria_Medicamento.models import CategoriaMedicamento


@admin.register(CategoriaMedicamento)
class CategoriaMedicamentoAdmin(admin.ModelAdmin):
  list_display = ('id', 'nombre_categoria', 'estado', 'fecha_creacion')
  search_fields = ('nombre_categoria',)
  list_filter = ('estado',)