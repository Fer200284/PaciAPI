from django.db import models


class Especialidades(models.Model):
  # El ID (IdEspecialidad) lo crea Django automáticamente como Primary Key autoincrementable (IDENTITY)

  nombre_especialidad = models.CharField(
      max_length=150,
      unique=True,
      db_column="NombreEspecialidad",  # Respeta exactamente el nombre de la columna en tu SQL
  )
  fecha_creacion = models.DateTimeField(
      auto_now_add=True,
      db_column="FechaCreacion",  # Equivalente a DEFAULT GETDATE()
  )
  estado = models.BooleanField(
      default=True,
      db_column="Estado",  # Equivalente a BIT NOT NULL DEFAULT 1
  )

  class Meta:
    db_table = "Especialidades"  # Mantiene el nombre exacto de la tabla en tu base de datos SQL
    verbose_name = "Especialidad"
    verbose_name_plural = "Especialidades"

  def __str__(self):
    return self.nombre_especialidad