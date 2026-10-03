from django.contrib import admin
from apps.catalogos.Sector. models import Sector


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
  list_display = (
      'id',
      'numero_sector',
      'nombre_sector',
      'zona_procedencia',
      'estado',
  )
  search_fields = ('nombre_sector', 'numero_sector')
  list_filter = ('estado', 'zona_procedencia')