from django.contrib import admin
from apps.catalogos.Patologias_Cronicas.models import PatologiasCronicas


@admin.register(PatologiasCronicas)
class PatologiasCronicasAdmin(admin.ModelAdmin):
  list_display = ('id', 'nombre_patologia', 'estado', 'fecha_creacion')
  search_fields = ('nombre_patologia',)
  list_filter = ('estado',)