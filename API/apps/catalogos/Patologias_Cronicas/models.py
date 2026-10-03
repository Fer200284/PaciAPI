from django.db import models


class PatologiasCronicas(models.Model):
  # Django crea automáticamente el campo ID (IDPatologiaCRonica) como Primary Key autoincrementable

  nombre_patologia = models.CharField(
      max_length=150,
      unique=True,
      db_column="Nombre_patologia",  # NVARCHAR(150) UNIQUE NOT NULL
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
    db_table = "Patologias_Cronicas"  # Nombre exacto de la tabla en tu base de datos SQL
    verbose_name = "Patología Crónica"
    verbose_name_plural = "Patologías Crónicas"

  def __str__(self):
    return self.nombre_patologia