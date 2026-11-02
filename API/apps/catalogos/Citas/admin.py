from django.contrib import admin

from .models import Citas


@admin.register(Citas)
class CitasAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "id_paciente",
        "id_medico",
        "fecha_hora_cita",
        "estado",
        "fecha_atencion_real",
    )
    list_filter = ("estado",)
    search_fields = (
        "id_paciente__nombre",
        "id_paciente__apellidos",
        "id_medico__nombre",
        "id_medico__apellidos",
    )
