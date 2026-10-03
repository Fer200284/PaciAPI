from django.contrib import admin
from apps.catalogos.TipoEntrada.models import TipoEntrada


@admin.register(TipoEntrada)
class TipoEntradaAdmin(admin.ModelAdmin):
  list_display = ('id', 'codigo', 'descripcion', 'estado')
  search_fields = ('codigo', 'descripcion')
  list_filter = ('estado',)