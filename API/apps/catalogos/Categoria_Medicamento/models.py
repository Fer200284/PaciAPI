from django.db import models


class CategoriaMedicamento(models.Model):
  # Django crea automáticamente el campo ID (IdCategoriaMedicamento) como Primary Key autoincrementable

  nombre_categoria = models.CharField(
      max_length=250,
      unique=True,
      db_column="NombreCategoria",  # NVARCHAR(250) NOT NULL UNIQUE
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
    db_table = (  # Nombre exacto de la tabla en tu base de datos SQL
        "Categoria_Medicamento"
    )
    verbose_name = "Categoría de Medicamento"
    verbose_name_plural = "Categorías de Medicamentos"

  def __str__(self):
    return self.nombre_categoria