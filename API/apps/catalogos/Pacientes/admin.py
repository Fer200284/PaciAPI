from django.contrib import admin
from apps.catalogos.Pacientes. models import Pacientes


@admin.register(Pacientes)
class PacientesAdmin(admin.ModelAdmin):
  list_display = (
      'id',
      'nombre',
      'apellidos',
      'cedula',
      'celular',
      'sexo',
      'id_sector',
      'estado',
  )
  search_fields = ('nombre', 'apellidos', 'cedula')
  list_filter = ('estado', 'sexo', 'id_sector')