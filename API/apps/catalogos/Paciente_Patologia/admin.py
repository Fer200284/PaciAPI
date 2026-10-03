from django.contrib import admin
from apps.catalogos.Paciente_Patologia.models import PacientePatologia


@admin.register(PacientePatologia)
class PacientePatologiaAdmin(admin.ModelAdmin):
  list_display = (
      'id',
      'id_paciente',
      'id_patologia_cronica',
      'fecha_de_diagnostico',
      'estado',
  )
  list_filter = ('estado', 'id_patologia_cronica')