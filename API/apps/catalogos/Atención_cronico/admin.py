from django.contrib import admin
from apps.catalogos.Atención_cronico.models import AtencionCronico


@admin.register(AtencionCronico)
class AtencionCronicoAdmin(admin.ModelAdmin):
  list_display = (
      'id',
      'fecha_atencion',
      'id_paciente_patologia',
      'id_medico',
      'peso',
      'talla',
      'asistio',
  )
  list_filter = ('asistio', 'consulta_especializada', 'fecha_atencion')