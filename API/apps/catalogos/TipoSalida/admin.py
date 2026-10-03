from django.contrib import admin
from apps.catalogos.TipoSalida. models import TipoSalida


@admin.register(TipoSalida)
class TipoSalidaAdmin(admin.ModelAdmin):
  list_display = ('id', 'codigo', 'descripcion', 'estado')
  search_fields = ('codigo', 'descripcion')
  list_filter = ('estado',)