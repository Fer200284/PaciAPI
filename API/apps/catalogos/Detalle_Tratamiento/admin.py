from django.contrib import admin
from apps.catalogos.Detalle_Tratamiento. models import DetalleTratamiento


@admin.register(DetalleTratamiento)
class DetalleTratamientoAdmin(admin.ModelAdmin):
  list_display = (
      'id',
      'id_tratamiento',
      'id_medicamento',
      'cantidad_entregada',
  )
  list_filter = ('id_medicamento',)