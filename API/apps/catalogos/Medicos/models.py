from django.core.validators import RegexValidator
from django.db import models


class Medicos(models.Model):
  # Restricción equivalente a tu CHECK de SQL (exactamente 8 dígitos numéricos)
  solo_ocho_numeros = RegexValidator(
      regex=r"^\d{8}$", message="El celular debe contener exactamente 8 dígitos."
  )

  # Relación con la app Especialidades usando cadena de texto (Lazy Relationship)
  id_especialidad = models.ForeignKey(
      "Especialidades.Especialidades",
      on_delete=models.PROTECT,
      db_column="IdEspecialidad",
  )
  nombre = models.CharField(max_length=150)
  apellidos = models.CharField(max_length=150)
  celular = models.CharField(max_length=8, validators=[solo_ocho_numeros])
  codigo_minsa = models.CharField(max_length=15, unique=True)
  fecha_creacion = models.DateTimeField(auto_now_add=True)
  estado = models.BooleanField(default=True)

  class Meta:
    db_table = "Medicos"
    verbose_name = "Médico"
    verbose_name_plural = "Médicos"

  def __str__(self):
    return f"Dr. {self.nombre} {self.apellidos} ({self.codigo_minsa})"