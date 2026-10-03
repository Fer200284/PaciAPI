from django.contrib import admin
from apps.catalogos.Tratamiento. models import Tratamiento


@admin.register(Tratamiento)
class TratamientoAdmin(admin.ModelAdmin):
  list_display = (
      'id',
      'id_atencion_cronico',
      'fecha_tratamiento',
      'observaciones',
  )
  list_filter = ('fecha_tratamiento',)